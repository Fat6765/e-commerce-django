from .services import Cart


def cart_summary(request):
    cart = Cart(request)
    return {
        "cart_items_count": cart.total_quantity,
    }
