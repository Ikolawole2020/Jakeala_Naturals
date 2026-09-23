"""Account routes, mounted under ``/api/`` by ``config.urls``."""

from django.urls import path

from . import views

urlpatterns = [
    path("auth/register/", views.register, name="auth-register"),
    path("auth/verify-email/", views.verify_email, name="auth-verify-email"),
    path("auth/resend-code/", views.resend_code, name="auth-resend-code"),
    path("auth/login/", views.login, name="auth-login"),
    path("auth/logout/", views.logout, name="auth-logout"),
    path("auth/me/", views.me, name="auth-me"),
    path("auth/password/change/", views.change_password, name="auth-password-change"),
    path("auth/password/reset/", views.password_reset_request, name="auth-password-reset"),
    path(
        "auth/password/reset/confirm/",
        views.password_reset_confirm,
        name="auth-password-reset-confirm",
    ),
]
