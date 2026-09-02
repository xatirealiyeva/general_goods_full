import uuid
from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies=[("catalog","0004_catalog_extensions"),("inventory","0001_initial")]
    operations=[migrations.CreateModel(name="LowStockAlert",fields=[("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True)),("quantity",models.PositiveIntegerField()),("acknowledged",models.BooleanField(default=False)),("variant",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="low_stock_alerts",to="catalog.productvariant"))],options={"db_table":"low_stock_alerts"})]
