from django.core import mail
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.test.utils import override_settings

from .models import Category, Order, OrderItem, Product


class OrderViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="client", password="secret123")
        self.other_user = User.objects.create_user(username="other", password="secret123")
        self.admin_user = User.objects.create_user(
            username="admin",
            password="secret123",
            is_staff=True,
        )
        category = Category.objects.create(name="Smartphones")
        product = Product.objects.create(
            name="Phone X",
            description="Description",
            price="999.00",
            stock=10,
            category=category,
        )
        self.order = Order.objects.create(
            user=self.user,
            customer_name="Client Connecte",
            customer_email="client@example.com",
            customer_phone="+212600000001",
            reference="CMD-2001",
            status=Order.Status.CONFIRMED,
            shipping_address="1 Avenue Hassan II",
        )
        OrderItem.objects.create(order=self.order, product=product, quantity=1, unit_price="999.00")
        self.other_order = Order.objects.create(
            user=self.other_user,
            customer_name="Autre Client",
            customer_email="other@example.com",
            customer_phone="+212600000002",
            reference="CMD-2002",
            status=Order.Status.PENDING,
            shipping_address="2 Avenue Hassan II",
        )

    def test_order_list_requires_authentication(self):
        response = self.client.get(reverse("order_list"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('order_list')}")

    def test_order_list_only_shows_logged_in_user_orders(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("order_list"))

        self.assertContains(response, "CMD-2001")
        self.assertNotContains(response, "CMD-2002")

    def test_order_detail_forbids_access_to_other_users_orders(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("order_detail", args=[self.other_order.pk]))

        self.assertEqual(response.status_code, 404)

    def test_staff_user_can_see_all_orders_and_customer_coordinates(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("order_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CMD-2001")
        self.assertContains(response, "CMD-2002")
        self.assertContains(response, "+212600000001")
        self.assertContains(response, "other@example.com")

    def test_staff_user_can_open_order_detail_with_customer_coordinates(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("order_detail", args=[self.other_order.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Autre Client")
        self.assertContains(response, "other@example.com")
        self.assertContains(response, "+212600000002")


class CartAndCheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="checkout-user",
            email="checkout@example.com",
            password="secret123",
        )
        category = Category.objects.create(name="Accessoires")
        self.product = Product.objects.create(
            name="Casque audio",
            description="Son immersif",
            price="199.00",
            stock=3,
            category=category,
        )

    def test_cart_add_stores_multiple_quantities_in_session(self):
        response = self.client.post(
            reverse("cart_add", args=[self.product.pk]),
            {"quantity": 2, "next": reverse("cart_detail")},
        )

        self.assertRedirects(response, reverse("cart_detail"))
        self.assertEqual(self.client.session["cart"][str(self.product.pk)], 2)

    def test_guest_can_access_checkout(self):
        session = self.client.session
        session["cart"] = {str(self.product.pk): 1}
        session.save()

        response = self.client.get(reverse("checkout"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gmail")
        self.assertContains(response, "Telephone")
        self.assertContains(response, "Ville")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_DELIVERY_ENABLED=True,
        DEFAULT_FROM_EMAIL="shop@example.com",
    )
    def test_checkout_creates_order_updates_stock_and_sends_email(self):
        session = self.client.session
        session["cart"] = {str(self.product.pk): 2}
        session.save()
        self.client.force_login(self.user)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("checkout"),
                {
                    "customer_name": "Client Connecte",
                    "customer_email": "checkout@example.com",
                    "customer_phone": "+212600000003",
                    "shipping_address": "10 Rue des Testeurs, Casablanca",
                    "city": "Casablanca",
                },
            )

        order = Order.objects.get(user=self.user)
        self.product.refresh_from_db()

        self.assertRedirects(response, reverse("order_detail", args=[order.pk]))
        self.assertEqual(self.product.stock, 1)
        self.assertFalse(self.client.session.get("cart"))
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.customer_phone, "+212600000003")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(order.reference, mail.outbox[0].subject)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_DELIVERY_ENABLED=True,
        DEFAULT_FROM_EMAIL="shop@example.com",
    )
    def test_guest_checkout_creates_order_without_user(self):
        session = self.client.session
        session["cart"] = {str(self.product.pk): 1}
        session.save()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("checkout"),
                {
                    "customer_name": "Client Invite",
                    "customer_email": "invite@example.com",
                    "customer_phone": "+212600000004",
                    "shipping_address": "20 Rue des Invites, Rabat",
                    "city": "Rabat",
                },
            )

        order = Order.objects.get(customer_email="invite@example.com")
        self.product.refresh_from_db()

        self.assertIsNone(order.user)
        self.assertEqual(order.customer_phone, "+212600000004")
        self.assertRedirects(response, reverse("checkout_success"))
        self.assertEqual(self.product.stock, 2)
        self.assertEqual(len(mail.outbox), 1)

    def test_checkout_rejects_quantities_above_stock(self):
        session = self.client.session
        session["cart"] = {str(self.product.pk): 5}
        session.save()

        response = self.client.post(
            reverse("checkout"),
            {
                "customer_name": "Client Invite",
                "customer_email": "invite@example.com",
                "customer_phone": "+212600000005",
                "shipping_address": "10 Rue des Testeurs, Casablanca",
                "city": "Casablanca",
            },
            follow=True,
        )

        self.product.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stock insuffisant")
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(self.product.stock, 3)
