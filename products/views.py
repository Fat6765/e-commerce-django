from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views import View

from .forms import AddToCartForm, CheckoutForm
from .models import Category, Order, Product
from .services import Cart, create_order_from_cart


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
    return render(request, "product_list.html", {"products": products, "add_to_cart_form": AddToCartForm()})


def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related("category"), pk=pk)
    return render(
        request,
        "product_detail.html",
        {"product": product, "add_to_cart_form": AddToCartForm()},
    )


def category_list(request):
    categories = Category.objects.order_by("name")
    return render(request, "category_list.html", {"categories": categories})


def category_detail(request, pk):
    category = get_object_or_404(
        Category.objects.prefetch_related("products").order_by("name"),
        pk=pk,
    )
    return render(
        request,
        "category_details.html",
        {"category": category, "add_to_cart_form": AddToCartForm()},
    )


def cart_detail(request):
    cart = Cart(request)
    return render(
        request,
        "cart/detail.html",
        {
            "cart": cart,
            "cart_items": cart.items(),
            "cart_total": cart.total_price(),
        },
    )


@require_POST
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = AddToCartForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Quantite invalide.")
        return redirect("product_detail", pk=pk)

    if product.stock <= 0:
        messages.error(request, "Ce produit est actuellement en rupture de stock.")
        return redirect("product_detail", pk=pk)

    cart = Cart(request)
    requested_quantity = form.cleaned_data["quantity"]
    cart.add(product=product, quantity=requested_quantity)
    if requested_quantity > product.stock:
        messages.warning(
            request,
            f"Le stock de {product.name} est limite a {product.stock} article(s).",
        )
    else:
        messages.success(request, f"{product.name} a ete ajoute au panier.")
    return redirect(request.POST.get("next") or "cart_detail")


@require_POST
def cart_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = AddToCartForm(request.POST)
    if form.is_valid():
        Cart(request).add(product=product, quantity=form.cleaned_data["quantity"], replace=True)
        messages.success(request, f"Quantite mise a jour pour {product.name}.")
    else:
        messages.error(request, "Impossible de mettre a jour la quantite.")
    return redirect("cart_detail")


@require_POST
def cart_remove(request, pk):
    product = get_object_or_404(Product, pk=pk)
    Cart(request).remove(product)
    messages.info(request, f"{product.name} a ete retire du panier.")
    return redirect("cart_detail")


def checkout(request):
    cart = Cart(request)
    if cart.is_empty():
        messages.info(request, "Votre panier est vide.")
        return redirect("cart_detail")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = create_order_from_cart(
                    user=request.user if request.user.is_authenticated else None,
                    cart=cart,
                    customer_name=form.cleaned_data["customer_name"],
                    customer_email=form.cleaned_data["customer_email"],
                    customer_phone=form.cleaned_data["customer_phone"],
                    shipping_address=(
                        f'{form.cleaned_data["shipping_address"]}, {form.cleaned_data["city"]}'
                    ),
                )
            except ValueError as exc:
                messages.error(request, str(exc))
            else:
                cart.clear()
                confirmation_message = f"Commande {order.reference} confirmee."
                if settings.EMAIL_DELIVERY_ENABLED:
                    confirmation_message += " Un email de confirmation vous a ete envoye."
                else:
                    confirmation_message += " Configurez SendGrid ou Mailgun dans l'environnement pour l'envoi automatique des emails."
                messages.success(request, confirmation_message)
                if request.user.is_authenticated:
                    return redirect("order_detail", pk=order.pk)
                request.session["last_guest_order_reference"] = order.reference
                request.session["last_guest_order_email"] = order.customer_email
                request.session.modified = True
                return redirect("checkout_success")
    else:
        initial = {}
        if request.user.is_authenticated:
            full_name = request.user.get_full_name().strip()
            initial = {
                "customer_name": full_name or request.user.username,
                "customer_email": request.user.email,
                "customer_phone": "",
                "city": "",
            }
        form = CheckoutForm(initial=initial)

    return render(
        request,
        "cart/checkout.html",
        {
            "form": form,
            "cart": cart,
            "cart_items": cart.items(),
            "cart_total": cart.total_price(),
        },
    )


def checkout_success(request):
    reference = request.session.get("last_guest_order_reference")
    email = request.session.get("last_guest_order_email")
    if not reference:
        return redirect("product_list")
    return render(
        request,
        "cart/success.html",
        {"reference": reference, "customer_email": email},
    )


@login_required
def order_list(request):
    order_queryset = Order.objects.prefetch_related("items__product").order_by("-created_at")
    orders = order_queryset if request.user.is_staff else order_queryset.filter(user=request.user)
    return render(
        request,
        "orders/order_list.html",
        {"orders": orders, "is_admin_order_view": request.user.is_staff},
    )


@login_required
def order_detail(request, pk):
    order_queryset = Order.objects.prefetch_related("items__product")
    if not request.user.is_staff:
        order_queryset = order_queryset.filter(user=request.user)
    order = get_object_or_404(order_queryset, pk=pk)
    return render(
        request,
        "orders/order_detail.html",
        {"order": order, "is_admin_order_view": request.user.is_staff},
    )
