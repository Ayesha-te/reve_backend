from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0027_product_sort_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="dimension_images",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
