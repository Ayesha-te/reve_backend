from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_productsize_price_delta'),
    ]

    operations = [
        migrations.AddField(
            model_name='productcolor',
            name='image_url',
            field=models.URLField(max_length=1000, blank=True),
        ),
    ]
