from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0021_product_custom_info_sections_product_delivery_title_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='show_size_icons',
            field=models.BooleanField(default=True),
        ),
    ]

