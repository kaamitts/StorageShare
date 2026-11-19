from datetime import timedelta

from django.db import migrations, models
from django.db.models import F, Value

import bookings.models


def backfill_payment_deadlines(apps, schema_editor):
    Booking = apps.get_model("bookings", "Booking")
    Booking.objects.update(
        payment_expires_at=F("created_at") + Value(timedelta(minutes=15)),
    )


class Migration(migrations.Migration):
    dependencies = [("bookings", "0003_booking_checked_in_out_at")]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="payment_expires_at",
            field=models.DateTimeField(null=True),
        ),
        migrations.RunPython(backfill_payment_deadlines, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="booking",
            name="payment_expires_at",
            field=models.DateTimeField(default=bookings.models.default_payment_expires_at),
        ),
        migrations.RemoveConstraint(
            model_name="booking",
            name="booking_status_valid",
        ),
        migrations.AlterField(
            model_name="booking",
            name="status",
            field=models.CharField(
                choices=[
                    ("awaiting_payment", "Awaiting payment"),
                    ("expired", "Expired"),
                    ("confirmed", "Confirmed"),
                    ("checked_in", "Checked in"),
                    ("completed", "Completed"),
                    ("cancelled", "Cancelled"),
                ],
                default="awaiting_payment",
                max_length=20,
            ),
        ),
        migrations.AddIndex(
            model_name="booking",
            index=models.Index(
                fields=["status", "payment_expires_at"],
                name="booking_status_expiry_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="booking",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    status__in=[
                        "awaiting_payment", "expired", "confirmed",
                        "checked_in", "completed", "cancelled",
                    ],
                ),
                name="booking_status_valid",
            ),
        ),
    ]
