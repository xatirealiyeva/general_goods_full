from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies=[("catalog","0004_catalog_extensions"),("orders","0003_refunds_disputes")]
    operations=[migrations.AddField(model_name="order",name="discount_amount",field=models.DecimalField(decimal_places=2,default=0,max_digits=12)),migrations.AddField(model_name="order",name="discount_code",field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="orders",to="catalog.discountcode"))]
