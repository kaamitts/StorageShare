"""Real competing requests. Run these tests against PostgreSQL, not SQLite."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time, timedelta
from decimal import Decimal
from queue import Queue
from threading import Barrier
from time import monotonic, sleep
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import connection, connections, transaction
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.models import Booking
from storage.models import District, StoragePoint


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
class BookingConcurrencyTests(TransactionTestCase):
    def setUp(self):
        user_model = get_user_model()
        self.traveler = user_model.objects.create_user(email="race-traveler@example.com")
        partner = user_model.objects.create_user(email="race-partner@example.com", role="partner")
        self.point = StoragePoint.objects.create(
            partner=partner, name="Last space", address="Test address",
            district=District.MEDEU, price_per_bag_per_hour=Decimal("300.00"),
            capacity_bags=1, opens_at=time(8), closes_at=time(23),
        )
        tomorrow = timezone.localdate() + timedelta(days=2)
        start = timezone.make_aware(datetime.combine(tomorrow, time(10)))
        self.payload = {
            "storage_point": self.point.pk,
            "drop_off_at": start.isoformat(),
            "pick_up_at": (start + timedelta(hours=2)).isoformat(),
            "bags_count": 1,
        }
        self.url = reverse("bookings:booking-create")

    def run_competing_requests(self):
        barrier = Barrier(3)
        worker_pids = Queue()

        def request():
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET lock_timeout = '15s'")
                    cursor.execute("SELECT pg_backend_pid()")
                    worker_pids.put(cursor.fetchone()[0])
                client = APIClient()
                client.force_authenticate(self.traveler)
                barrier.wait(timeout=10)
                response = client.post(self.url, self.payload, format="json")
                return response.status_code, response.data
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            # Hold the parent lock so both independent connections must wait
            # before checking capacity. This also covers an empty booking table.
            with transaction.atomic():
                StoragePoint.objects.select_for_update().get(pk=self.point.pk)
                futures = [pool.submit(request), pool.submit(request)]
                pids = [worker_pids.get(timeout=10), worker_pids.get(timeout=10)]
                barrier.wait(timeout=10)
                deadline = monotonic() + 5
                waiting = 0
                while monotonic() < deadline:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT pg_stat_clear_snapshot()")
                        cursor.execute(
                            "SELECT count(*) FROM pg_stat_activity "
                            "WHERE pid = ANY(%s) AND wait_event_type = 'Lock' "
                            "AND query LIKE %s",
                            [pids, "%FOR UPDATE%"],
                        )
                        waiting = cursor.fetchone()[0]
                    if waiting == 2:
                        break
                    sleep(0.02)
            results = [future.result(timeout=20) for future in futures]
        self.assertEqual(waiting, 2, "Both requests must wait on the database row lock")
        return results

    def test_only_one_request_gets_the_last_space(self):
        results = self.run_competing_requests()
        self.assertEqual(sorted(code for code, data in results), [201, 400], results)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(Booking.objects.get().bags_count, 1)

    def test_both_requests_succeed_when_two_spaces_are_available(self):
        self.point.capacity_bags = 2
        self.point.save(update_fields=["capacity_bags"])
        results = self.run_competing_requests()
        self.assertEqual(sorted(code for code, data in results), [201, 201], results)
        self.assertEqual(Booking.objects.count(), 2)
