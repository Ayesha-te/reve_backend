from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0014_orderitem_dimension_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orderitem",
            name="style",
            field=models.TextField(blank=True, default=""),
        ),
    ]

