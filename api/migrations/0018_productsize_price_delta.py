from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_review_visibility_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='productsize',
            name='price_delta',
            field=models.DecimalField(max_digits=10, decimal_places=2, default=0.00),
        ),
    ]
