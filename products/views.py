from django.shortcuts import get_object_or_404, render
from django.views import View

from .models import Category, Product


def index(request):
    featured_categories = Category.objects.order_by("name")[:3]
    latest_products = Product.objects.select_related("category").order_by("-created_at")[:4]
    context = {
        "featured_categories": featured_categories,
        "latest_products": latest_products,
    }
    return render(request, "index.html", context)


class ProductView(View):
    def get(self, request):
        produits = ["hp", "mac", "toshiba", "samsung"]
        return render(request, "products.html", {"produits": produits})


def product_list(request):
    products = Product.objects.select_related("category").order_by("-created_at", "name")
    return render(request, "product_list.html", {"products": products})


def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related("category"), pk=pk)
    return render(request, "product_detail.html", {"product": product})


def category_list(request):
    categories = Category.objects.order_by("name")
    return render(request, "category_list.html", {"categories": categories})


def category_detail(request, pk):
    category = get_object_or_404(
        Category.objects.prefetch_related("products").order_by("name"),
        pk=pk,
    )
    return render(request, "category_details.html", {"category": category})
