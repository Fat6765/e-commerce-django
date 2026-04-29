from django.contrib import admin

from .models import EmailVerificationToken


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "is_verified", "created_at"]
    list_filter = ["is_verified", "created_at"]
    readonly_fields = ["token", "created_at"]
