"""
URL configuration for the SaaS platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include(('apps.accounts.urls', 'accounts'), namespace='accounts')),
    path('', include(('apps.orders.urls', 'orders'), namespace='orders')),
    path('customers/', include(('apps.customers.urls', 'customers'), namespace='customers')),
    path('services/', include(('apps.services.urls', 'services'), namespace='services')),
    path('finance/', include(('apps.finance.urls', 'finance'), namespace='finance')),
    path('loyalty/', include(('apps.loyalty.urls', 'loyalty'), namespace='loyalty')),
    path('billing/', include(('apps.billing.urls', 'billing'), namespace='billing')),
    path('appointments/', include(('apps.appointments.urls', 'appointments'), namespace='appointments')),
    path('commissions/', include(('apps.commissions.urls', 'commissions'), namespace='commissions')),
    path('portal/', include(('apps.portal.urls', 'portal'), namespace='portal')),
    path('api/v1/', include(('apps.api.urls', 'api'), namespace='api')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
