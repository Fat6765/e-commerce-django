from django.db import migrations, models
import django.db.models.deletion


def assign_default_category(apps, schema_editor):
    Category = apps.get_model("products", "Category")
    Product = apps.get_model("products", "Product")

    default_category, _ = Category.objects.get_or_create(
        name="Non classée",
        defaults={"description": "Catégorie créée automatiquement."},
    )
    Product.objects.filter(category__isnull=True).update(category=default_category)


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0003_update_category_fields"),
    ]

    operations = [
        migrations.RunPython(assign_default_category, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="product",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="products",
                to="products.category",
            ),
        ),
    ]
