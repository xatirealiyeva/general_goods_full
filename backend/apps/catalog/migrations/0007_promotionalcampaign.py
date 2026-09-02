import uuid
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[("catalog","0006_product_store")]
    operations=[migrations.CreateModel(name="PromotionalCampaign",fields=[("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True)),("name",models.CharField(max_length=150,unique=True)),("description",models.TextField(blank=True)),("discount_type",models.CharField(choices=[("PERCENTAGE","Percentage"),("FIXED","Fixed")],max_length=16)),("value",models.DecimalField(decimal_places=2,max_digits=12)),("starts_at",models.DateTimeField()),("ends_at",models.DateTimeField()),("is_active",models.BooleanField(default=True)),("categories",models.ManyToManyField(blank=True,related_name="campaigns",to="catalog.category")),("products",models.ManyToManyField(blank=True,related_name="campaigns",to="catalog.product"))],options={"db_table":"promotional_campaigns"})]
