from django.db import migrations, models


def replace_null_category_descriptions(apps, schema_editor):
    Category = apps.get_model("products", "Category")
    Category.objects.filter(description__isnull=True).update(description="")


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0002_category_product_category"),
    ]

    operations = [
        migrations.RunPython(
            replace_null_category_descriptions,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="category",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="category",
            name="name",
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
