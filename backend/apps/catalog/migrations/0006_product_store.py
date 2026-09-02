from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies=[("catalog", "0004_catalog_extensions"), ("customers", "0004_store")]
    operations=[migrations.AddField(model_name="product", name="store", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="products", to="customers.store"))]
