from django.urls import path

from . import views

urlpatterns = [
    path("payments/config/", views.payments_config, name="payments-config"),
    path("payments/initialize/", views.initialize_payment, name="payments-initialize"),
    path("payments/verify/", views.verify_payment, name="payments-verify"),
    path("payments/webhook/", views.paystack_webhook, name="payments-webhook"),
]
