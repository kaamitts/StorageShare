from django.db import migrations, models


DEMO_COORDINATES = {
    "Dostyk ave 85": ("43.255803", "76.955293"),
    "Abai ave 90": ("43.238267", "76.897971"),
    "Zheltoksan st 115": ("43.253082", "76.939583"),
    "Tole bi st 55": ("43.255464", "76.945639"),
    "Gogol st 40": ("43.259698", "76.954310"),
    "Satpaev st 22": ("43.236718", "76.928949"),
}


def backfill_demo_coordinates(apps, schema_editor):
    StoragePoint = apps.get_model("storage", "StoragePoint")
    for address, (latitude, longitude) in DEMO_COORDINATES.items():
        StoragePoint.objects.filter(address=address).filter(
            models.Q(latitude__isnull=True) | models.Q(longitude__isnull=True)
        ).update(latitude=latitude, longitude=longitude)


class Migration(migrations.Migration):

    dependencies = [
        ("storage", "0003_mark_legacy_all_day_points"),
    ]

    operations = [
        migrations.AddField(
            model_name="storagepoint",
            name="latitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                verbose_name="latitude",
            ),
        ),
        migrations.AddField(
            model_name="storagepoint",
            name="longitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                verbose_name="longitude",
            ),
        ),
        migrations.RunPython(backfill_demo_coordinates, migrations.RunPython.noop),
    ]
