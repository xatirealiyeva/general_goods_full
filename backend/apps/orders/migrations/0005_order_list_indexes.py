from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies=[("orders","0004_order_discount")]
    operations=[migrations.AddIndex(model_name="order",index=models.Index(fields=["customer","-created_at"],name="orders_customer_created_idx")),migrations.AddIndex(model_name="order",index=models.Index(fields=["status","-created_at"],name="orders_status_created_idx"))]
