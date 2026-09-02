import uuid
from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies=[("shipments","0001_initial")]
    operations=[migrations.CreateModel(name="ShippingZone",fields=[("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True)),("name",models.CharField(max_length=100,unique=True)),("regions",models.JSONField(default=list)),("delivery_fee",models.DecimalField(decimal_places=2,max_digits=10)),("estimated_days",models.PositiveIntegerField(default=3)),("is_active",models.BooleanField(default=True))],options={"db_table":"shipping_zones"}),migrations.AddField(model_name="shipment",name="shipping_zone",field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="shipments",to="shipments.shippingzone"))]
