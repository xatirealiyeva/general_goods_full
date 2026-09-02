import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("catalog", "0003_alter_product_options")]
    operations = [
        migrations.CreateModel(name="Brand", fields=[("id", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, editable=False)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("is_deleted", models.BooleanField(default=False)), ("deleted_at", models.DateTimeField(blank=True, null=True)), ("name", models.CharField(max_length=100, unique=True)), ("slug", models.SlugField(max_length=120, unique=True))], options={"db_table":"brands"}),
        migrations.CreateModel(name="Tag", fields=[("id", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, editable=False)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("is_deleted", models.BooleanField(default=False)), ("deleted_at", models.DateTimeField(blank=True, null=True)), ("name", models.CharField(max_length=64, unique=True)), ("slug", models.SlugField(max_length=80, unique=True))], options={"db_table":"tags"}),
        migrations.AddField(model_name="category", name="status", field=models.CharField(choices=[("DRAFT","Draft"),("ACTIVE","Active"),("ARCHIVED","Archived")], default="DRAFT", max_length=16)),
        migrations.AddField(model_name="product", name="brand", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="products", to="catalog.brand")),
        migrations.AddField(model_name="product", name="tags", field=models.ManyToManyField(blank=True, related_name="products", to="catalog.tag")),
        migrations.CreateModel(name="DiscountCode", fields=[("id", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, editable=False)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("code", models.CharField(max_length=50, unique=True)), ("discount_type", models.CharField(choices=[("PERCENTAGE", "Percentage"), ("FIXED", "Fixed")], max_length=16)), ("value", models.DecimalField(decimal_places=2, max_digits=12)), ("starts_at", models.DateTimeField()), ("ends_at", models.DateTimeField()), ("is_active", models.BooleanField(default=True))], options={"db_table":"discount_codes"}),
    ]
