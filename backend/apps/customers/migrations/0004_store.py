import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("customers", "0003_wishlistitem"), ("sellers", "0002_initial")]
    operations = [migrations.CreateModel(name="Store", fields=[
        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
        ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
        ("name", models.CharField(max_length=200)), ("description", models.TextField(blank=True)),
        ("logo", models.ImageField(blank=True, upload_to="stores/")),
        ("status", models.CharField(choices=[("DRAFT", "Draft"), ("ACTIVE", "Active"), ("ARCHIVED", "Archived")], default="DRAFT", max_length=16)),
        ("owner", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="store", to="customers.customer")),
        ("seller", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="customer_store", to="sellers.seller")),
    ], options={"db_table": "customer_stores"})]
