from django.urls import path
from . import views

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("demo/", views.ProductView.as_view(), name="products"),
    path("<int:pk>/", views.product_detail, name="product_detail"),
    path("categories/", views.category_list, name="category_list"),
    path("categories/<int:pk>/", views.category_detail, name="category_detail"),    
]
