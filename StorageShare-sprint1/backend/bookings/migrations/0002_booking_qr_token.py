import secrets

from django.db import migrations, models

import bookings.models


def fill_qr_tokens(apps, schema_editor):
    Booking = apps.get_model("bookings", "Booking")
    for booking in Booking.objects.filter(qr_token__isnull=True).only("pk"):
        booking.qr_token = secrets.token_urlsafe(32)
        booking.save(update_fields=["qr_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0001_initial"),
    ]

    operations = [
        # A plain default would give every existing row the same value, so the
        # field is added empty, filled row by row, then made required and unique.
        migrations.AddField(
            model_name="booking",
            name="qr_token",
            field=models.CharField(editable=False, max_length=64, null=True),
        ),
        migrations.RunPython(fill_qr_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="booking",
            name="qr_token",
            field=models.CharField(
                default=bookings.models.generate_qr_token,
                editable=False,
                max_length=64,
                unique=True,
            ),
        ),
    ]
