from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0006_productfabric"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="faqs",
            field=models.JSONField(blank=True, default=list),
        ),
    ]

