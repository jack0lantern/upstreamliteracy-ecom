from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AddressViewSet, ClaimGuestView, ProfileView

router = DefaultRouter()
router.register(r"addresses", AddressViewSet, basename="address")

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="account-profile"),
    path("claim-guest/", ClaimGuestView.as_view(), name="account-claim-guest"),
    path("", include(router.urls)),
]
