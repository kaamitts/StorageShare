import time

from django.core.management.base import BaseCommand, CommandError

from bookings.services import expire_pending_bookings


class Command(BaseCommand):
    help = "Mark payment reservations older than 15 minutes as expired."

    def add_arguments(self, parser):
        parser.add_argument(
            "--loop",
            action="store_true",
            help="Run continuously instead of performing one cleanup pass.",
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=30,
            help="Seconds between cleanup passes when --loop is set (default: 30).",
        )

    def handle(self, *args, **options):
        interval = options["interval"]
        if interval < 1:
            raise CommandError("--interval must be at least 1 second.")

        while True:
            expired = expire_pending_bookings()
            self.stdout.write(f"Expired {expired} pending booking(s).")
            if not options["loop"]:
                return
            time.sleep(interval)
