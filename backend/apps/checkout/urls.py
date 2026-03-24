from django.urls import path
from . import views

urlpatterns = [
    path("sessions/", views.CreateSessionView.as_view()),
    path("sessions/<str:token>/", views.GetSessionView.as_view()),
    path("sessions/<str:token>/contact/", views.UpdateContactView.as_view()),
    path("sessions/<str:token>/address/", views.UpdateAddressView.as_view()),
    path("sessions/<str:token>/shipping/", views.UpdateShippingView.as_view()),
    path("sessions/<str:token>/payment/", views.UpdatePaymentView.as_view()),
    path("sessions/<str:token>/submit/", views.SubmitCheckoutView.as_view()),
    path("shipping-rates/", views.ShippingRatesView.as_view()),
    path("tax-estimate/", views.TaxEstimateView.as_view()),
]
