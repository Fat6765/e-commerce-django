from django.urls import path

from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("profile/", views.profile, name="profile"),
    path("change-password/", views.change_password, name="change_password"),
    path("verify-email/<str:token>/", views.verify_email, name="verify_email"),
    path("email-sent/", views.email_sent, name="email_sent"),
]
