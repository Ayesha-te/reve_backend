from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0005_alter_productcolor_options_remove_productcolor_image_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductFabric",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("image_url", models.URLField(max_length=1000)),
                (
                    "product",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fabrics", to="api.product"),
                ),
            ],
            options={
                "ordering": ["id"],
            },
        ),
    ]
