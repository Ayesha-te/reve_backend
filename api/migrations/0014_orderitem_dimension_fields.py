from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0013_alter_productstyle_icon_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="dimension",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="dimension_details",
            field=models.TextField(blank=True, default=""),
        ),
    ]

