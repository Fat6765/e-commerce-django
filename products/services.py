from decimal import Decimal
from secrets import token_hex

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from .models import Order, OrderItem, Product

try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    pymysql = None


CART_SESSION_ID = "cart"


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.setdefault(CART_SESSION_ID, {})

    def add(self, product, quantity=1, replace=False):
        product_id = str(product.id)
        existing_quantity = int(self.cart.get(product_id, 0))
        new_quantity = quantity if replace else existing_quantity + quantity
        self.cart[product_id] = max(1, min(new_quantity, product.stock))
        self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        self.session.pop(CART_SESSION_ID, None)
        self.session.modified = True
        self.cart = self.session.setdefault(CART_SESSION_ID, {})

    def save(self):
        self.session[CART_SESSION_ID] = self.cart
        self.session.modified = True

    def __len__(self):
        return sum(int(quantity) for quantity in self.cart.values())

    @property
    def total_quantity(self):
        return len(self)

    def product_ids(self):
        return [int(product_id) for product_id in self.cart.keys()]

    def items(self):
        products = Product.objects.filter(id__in=self.product_ids()).select_related("category")
        items = []
        for product in products:
            quantity = int(self.cart.get(str(product.id), 0))
            total_price = product.price * quantity
            items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "unit_price": product.price,
                    "total_price": total_price,
                }
            )
        return items

    def total_price(self):
        return sum((item["total_price"] for item in self.items()), Decimal("0.00"))

    def is_empty(self):
        return not self.cart


def build_order_reference():
    return f"CMD-{token_hex(4).upper()}"


def send_order_confirmation_email(order):
    if not getattr(settings, "EMAIL_DELIVERY_ENABLED", False):
        return

    item_lines = "\n".join(
        f"- {item.product.name} x{item.quantity} : {item.line_total} MAD"
        for item in order.items.select_related("product").all()
    )
    message = (
        f"Bonjour {order.customer_name},\n\n"
        f"Votre commande {order.reference} a bien ete enregistree.\n"
        f"Statut initial : {order.get_status_display()}\n\n"
        f"Telephone : {order.customer_phone}\n\n"
        f"Articles :\n{item_lines}\n\n"
        f"Adresse de livraison :\n{order.shipping_address}\n\n"
        f"Montant total : {order.total_amount} MAD\n\n"
        "Merci pour votre achat."
    )
    send_mail(
        subject=f"Confirmation de commande {order.reference}",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.customer_email],
    )


def create_order_from_cart(
    *,
    user,
    cart,
    shipping_address,
    customer_name,
    customer_email,
    customer_phone,
):
    product_ids = cart.product_ids()
    if not product_ids:
        raise ValueError("Le panier est vide.")

    with transaction.atomic():
        products = {
            product.id: product
            for product in Product.objects.select_for_update().filter(id__in=product_ids)
        }
        order = Order.objects.create(
            user=user,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            reference=build_order_reference(),
            shipping_address=shipping_address,
            status=Order.Status.CONFIRMED,
        )

        for product_id, quantity in cart.cart.items():
            product = products.get(int(product_id))
            requested_quantity = int(quantity)
            if product is None:
                raise ValueError("Un produit du panier n'existe plus.")
            if requested_quantity > product.stock:
                raise ValueError(
                    f"Stock insuffisant pour {product.name}. Il reste {product.stock} article(s)."
                )

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=requested_quantity,
                unit_price=product.price,
            )
            product.stock -= requested_quantity
            product.save(update_fields=["stock"])

        transaction.on_commit(lambda: send_order_confirmation_email(order))
        return order
