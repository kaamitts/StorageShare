from django.db import migrations, models


def mark_legacy_all_day_points(apps, schema_editor):
    StoragePoint = apps.get_model("storage", "StoragePoint")
    StoragePoint.objects.using(schema_editor.connection.alias).filter(
        opens_at=models.F("closes_at"),
    ).update(is_24_hours=True)


class Migration(migrations.Migration):

    dependencies = [
        ("storage", "0002_storagepoint_is_24_hours"),
    ]

    operations = [
        # Equal opening and closing times were already interpreted as all day.
        # Retain that meaning for rows created before the explicit flag existed.
        migrations.RunPython(mark_legacy_all_day_points, migrations.RunPython.noop),
    ]
