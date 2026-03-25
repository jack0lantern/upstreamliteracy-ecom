from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.health import health_check
from apps.core.live import live

urlpatterns = [
    path("admin/", admin.site.urls),
    path("live/", live),
    path("health/", health_check),
    path("api/v1/auth/", include("apps.accounts.urls_auth")),
    path("api/v1/accounts/", include("apps.accounts.urls_accounts")),
    path("api/v1/", include("apps.catalog.urls")),
    path("api/v1/inventory/", include("apps.inventory.urls")),
    path("api/v1/cart/", include("apps.cart.urls")),
    path("api/v1/checkout/", include("apps.checkout.urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
