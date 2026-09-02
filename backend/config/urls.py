"""
Root URL configuration. Groups all module APIs under /api/ as specified in
the technical documentation (section 9.1).
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/auth/", include("apps.authx.urls")),
    path("api/users/", include("apps.users.urls")),
    path("api/customers/", include("apps.customers.urls")),
    path("api/sellers/", include("apps.sellers.urls")),
    path("api/catalog/", include("apps.catalog.urls")),
    path("api/inventory/", include("apps.inventory.urls")),
    path("api/cart/", include("apps.cart.urls")),
    path("api/orders/", include("apps.orders.urls")),
    path("api/payments/", include("apps.payments.urls")),
    path("api/shipments/", include("apps.shipments.urls")),
    path("api/reviews/", include("apps.reviews.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
