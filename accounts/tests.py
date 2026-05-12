from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import RegisterForm
from .models import EmailVerificationToken
from products.models import Category, Order, OrderItem, Product


class RegisterFormTests(TestCase):
    def test_email_must_be_unique(self):
        User.objects.create_user(username="alice", email="alice@example.com", password="secret123")

        form = RegisterForm(
            data={
                "username": "bob",
                "email": "ALICE@example.com",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class SignupFlowTests(TestCase):
    def test_signup_creates_inactive_user_and_verification_token(self):
        response = self.client.post(
            reverse("signup"),
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            },
        )

        self.assertRedirects(response, reverse("email_sent"))
        user = User.objects.get(username="newuser")
        self.assertFalse(user.is_active)
        self.assertTrue(EmailVerificationToken.objects.filter(user=user).exists())


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="client",
            email="client@example.com",
            password="secret123",
        )
        category = Category.objects.create(name="Laptops")
        product = Product.objects.create(
            name="Laptop Pro",
            description="Puissant",
            price="1499.00",
            stock=5,
            category=category,
        )
        self.order = Order.objects.create(
            user=self.user,
            reference="CMD-1001",
            status=Order.Status.SHIPPED,
            shipping_address="12 Rue du Commerce, Casablanca",
        )
        OrderItem.objects.create(order=self.order, product=product, quantity=2, unit_price="1499.00")

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse("profile"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")

    def test_profile_exposes_recent_orders(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CMD-1001")
        self.assertEqual(list(response.context["recent_orders"]), [self.order])
