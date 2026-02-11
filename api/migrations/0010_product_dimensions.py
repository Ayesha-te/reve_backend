from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0009_productsize_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="dimensions",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
