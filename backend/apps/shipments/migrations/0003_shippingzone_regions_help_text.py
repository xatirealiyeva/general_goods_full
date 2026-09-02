from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("shipments", "0002_shippingzone")]

    operations = [
        migrations.AlterField(
            model_name="shippingzone",
            name="regions",
            field=models.JSONField(default=list, help_text="Cities or regions served by this zone."),
        ),
    ]
