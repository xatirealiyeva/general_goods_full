from django.db import migrations, models


def publish_pending_reviews(apps, schema_editor):
    Review = apps.get_model("reviews", "Review")
    Review.objects.filter(moderation_status="PENDING").update(moderation_status="APPROVED")


class Migration(migrations.Migration):
    dependencies = [("reviews", "0002_review_image")]

    operations = [
        migrations.AlterField(
            model_name="review",
            name="moderation_status",
            field=models.CharField(
                choices=[("PENDING", "Pending"), ("APPROVED", "Approved"), ("REJECTED", "Rejected")],
                default="APPROVED",
                max_length=16,
            ),
        ),
        migrations.RunPython(publish_pending_reviews, migrations.RunPython.noop),
    ]
