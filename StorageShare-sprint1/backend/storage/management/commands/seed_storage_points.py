"""Seed data for Sprint 1: six storage points across three districts.

    python manage.py seed_storage_points

Re-running it is safe: points are matched by name and updated, not duplicated.
The partner accounts are created with a known password so QA can log in as a
partner during manual testing.
"""

from datetime import time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from storage.models import District, StoragePoint

User = get_user_model()

PARTNER_PASSWORD = "SeedPartner2026"

PARTNERS = [
    ("hostel@example.com", "Almaty Hostel"),
    ("cafe@example.com", "Cafe Centre"),
    ("hotel@example.com", "Hotel Tien Shan"),
]

POINTS = [
    # (partner email, name, district, address, price/bag/hour, capacity, opens, closes, notes)
    ("hostel@example.com", "Almaty Hostel — reception", District.MEDEU,
     "Dostyk ave 85", "300.00", 10, time(8, 0), time(23, 0),
     "Locked room behind the reception desk, camera."),
    ("cafe@example.com", "Cafe Centre — back room", District.MEDEU,
     "Abai ave 90", "250.00", 6, time(10, 0), time(22, 0),
     "Staff-only room, door locked during service."),
    ("hotel@example.com", "Hotel Tien Shan — luggage room", District.MEDEU,
     "Zheltoksan st 115", "400.00", 20, time(0, 0), time(23, 59),
     "Dedicated luggage room, staffed 24/7."),
    ("hostel@example.com", "Almaty Hostel — basement", District.ALMALY,
     "Tole bi st 55", "200.00", 4, time(9, 0), time(21, 0),
     "Basement storage, padlocked cage."),
    ("cafe@example.com", "Cafe Centre — Almaly", District.ALMALY,
     "Gogol st 40", "250.00", 8, time(9, 0), time(21, 0),
     "Behind the counter, in sight of staff."),
    ("hotel@example.com", "Hotel Tien Shan — Bostandyk", District.BOSTANDYK,
     "Satpaev st 22", "350.00", 12, time(7, 0), time(23, 0),
     "Luggage room next to the lobby, camera."),
]


class Command(BaseCommand):
    help = "Create demo partners and six storage points in three districts."

    @transaction.atomic
    def handle(self, *args, **options):
        partners = {}
        for email, business_name in PARTNERS:
            partner, created = User.objects.get_or_create(
                email=email,
                defaults={"full_name": business_name, "role": User.Role.PARTNER},
            )
            if created:
                partner.set_password(PARTNER_PASSWORD)
                partner.save(update_fields=["password"])
            partners[email] = partner
            self.stdout.write(f"{'created' if created else 'exists '} partner {email}")

        for email, name, district, address, price, capacity, opens, closes, notes in POINTS:
            point, created = StoragePoint.objects.update_or_create(
                name=name,
                defaults={
                    "partner": partners[email],
                    "district": district,
                    "address": address,
                    "price_per_bag_per_hour": Decimal(price),
                    "capacity_bags": capacity,
                    "opens_at": opens,
                    "closes_at": closes,
                    "security_notes": notes,
                    "is_active": True,
                },
            )
            self.stdout.write(f"{'created' if created else 'updated'} {point}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone: {User.objects.filter(role=User.Role.PARTNER).count()} partners, "
            f"{StoragePoint.objects.count()} storage points.\n"
            f"Partner password: {PARTNER_PASSWORD}"
        ))
