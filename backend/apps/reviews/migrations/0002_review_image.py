from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reviews", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="review",
            name="image",
            field=models.ImageField(blank=True, upload_to="reviews/"),
        ),
    ]
