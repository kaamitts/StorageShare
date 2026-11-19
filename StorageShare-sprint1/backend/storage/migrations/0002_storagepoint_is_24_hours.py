from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("storage", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="storagepoint",
            name="is_24_hours",
            field=models.BooleanField(
                default=False,
                help_text="The point accepts handovers at any time of day.",
                verbose_name="open 24 hours",
            ),
        ),
    ]
