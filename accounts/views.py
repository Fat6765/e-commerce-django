from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import RegisterForm, ChangePasswordForm
from .models import EmailVerificationToken
from products.models import Order


def signup(request):
    if request.user.is_authenticated:
        return redirect("profile")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.email = form.cleaned_data["email"]
            user.save()
            
            # Create verification token
            verification_token = EmailVerificationToken.objects.create(user=user)
            
            # Send verification email
            verification_url = request.build_absolute_uri(
                reverse("verify_email", kwargs={"token": verification_token.token})
            )
            send_mail(
                subject="Confirmez votre adresse email",
                message=f"Bonjour {user.username},\n\n"
                        f"Veuillez confirmer votre adresse email en cliquant sur le lien suivant:\n\n"
                        f"{verification_url}\n\n"
                        f"Cordialement,\n"
                        f"L'equipe ecommerce",
                html_message=f"""<html><body>
                    <h2>Confirmez votre adresse email</h2>
                    <p>Bonjour {user.username},</p>
                    <p>Veuillez confirmer votre adresse email en cliquant sur le lien suivant:</p>
                    <a href="{verification_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Confirmer mon email</a>
                    <p>Ou copiez ce lien: {verification_url}</p>
                    <p>Cordialement,<br/>L'equipe ecommerce</p>
                </body></html>""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
            if settings.EMAIL_DELIVERY_ENABLED:
                messages.success(
                    request,
                    "Votre compte a ete cree. Un email de confirmation vient d'etre envoye.",
                )
            else:
                messages.warning(
                    request,
                    "Votre compte a ete cree, mais l'envoi email n'est pas encore configure. "
                    "Ajoutez les identifiants SMTP dans ecommerce/.env pour envoyer le lien de confirmation.",
                )
            return redirect("email_sent")
    else:
        form = RegisterForm()

    return render(request, "registration/signup.html", {"form": form})


@login_required
def profile(request):
    recent_orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")[:5]
    )
    return render(request, "registration/profile.html", {"recent_orders": recent_orders})


def email_sent(request):
    return render(request, "registration/email_sent.html")


@login_required
def change_password(request):
    if request.method == "POST":
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Votre mot de passe a ete change avec succes.")
            return redirect("profile")
    else:
        form = ChangePasswordForm(request.user)

    return render(request, "registration/change_password.html", {"form": form})


def verify_email(request, token):
    try:
        verification_token = EmailVerificationToken.objects.get(token=token)
        if verification_token.is_verified:
            messages.info(request, "Votre email a deja ete confirme.")
            return redirect("login")
        
        # Mark token as verified and activate user
        verification_token.is_verified = True
        verification_token.save()
        
        user = verification_token.user
        user.is_active = True
        user.save()
        
        messages.success(
            request,
            "Votre email a ete confirme avec succes. Vous pouvez maintenant vous connecter."
        )
        return redirect("login")
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, "Le lien de verification est invalide ou expire.")
        return redirect("login")
