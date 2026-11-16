from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0002_booking_qr_token"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="checked_in_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="booking",
            name="checked_out_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
