from django.contrib import admin

from .models import Category, Product


admin.site.site_header = "Administration Ecommerce"
admin.site.site_title = "Ecommerce Admin"
admin.site.index_title = "Gestion de la boutique"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "product_count", "created_at")
    ordering = ("name",)
    search_fields = ("name",)
    readonly_fields = ("created_at",)
    list_per_page = 20

    fieldsets = (
        ("Informations", {"fields": ("name", "description")}),
        ("Historique", {"fields": ("created_at",)}),
    )

    @admin.display(description="Produits")
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock_status", "stock", "category", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("name", "description", "category__name")
    ordering = ("-created_at", "name")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("category",)
    list_select_related = ("category",)
    list_per_page = 20

    fieldsets = (
        ("Produit", {"fields": ("name", "description", "category")}),
        ("Commercial", {"fields": ("price", "stock", "image")}),
        ("Historique", {"fields": ("created_at",)}),
    )

    @admin.display(description="Disponibilite")
    def stock_status(self, obj):
        return "En stock" if obj.stock > 0 else "Rupture"
