import uuid
from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies=[("catalog","0004_catalog_extensions"),("customers","0002_initial")]
    operations=[migrations.CreateModel(name="WishlistItem",fields=[("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True)),("customer",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="wishlist_items",to="customers.customer")),("product",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="wishlisted_by",to="catalog.product"))],options={"db_table":"wishlist_items","unique_together":{("customer","product")}})]
