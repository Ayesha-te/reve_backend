from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0026_productmattress_price_both_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="sort_order",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name="product",
            options={"ordering": ["sort_order", "-created_at"]},
        ),
    ]

