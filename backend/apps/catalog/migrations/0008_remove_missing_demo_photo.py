from django.db import migrations


def remove_missing_demo_photo(apps, schema_editor):
    # A legacy demo row references products/photo.jpg, which is not shipped in
    # MEDIA_ROOT. Remove only that invalid relation; real uploaded images are
    # retained unchanged.
    ProductImage = apps.get_model("catalog", "ProductImage")
    ProductImage.objects.filter(image="products/photo.jpg").delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0007_promotionalcampaign")]

    operations = [migrations.RunPython(remove_missing_demo_photo, migrations.RunPython.noop)]
