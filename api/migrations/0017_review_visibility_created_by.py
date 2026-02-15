from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0016_orderitem_extras_total_orderitem_include_dimension_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name="review",
            old_name="approved",
            new_name="is_visible",
        ),
        migrations.AddField(
            model_name="review",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reviews",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
