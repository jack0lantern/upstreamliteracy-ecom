from django.urls import path
from . import views

urlpatterns = [
    path("intent/", views.CreatePaymentIntentView.as_view()),
    path("<uuid:pk>/refunds/", views.CreateRefundView.as_view()),
    path("webhooks/stripe/", views.StripeWebhookView.as_view()),
]
