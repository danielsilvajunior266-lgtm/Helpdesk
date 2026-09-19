from django.urls import path
from apps.billing import views

urlpatterns = [
    path('', views.invoice_list, name='list'),
    path('customers/add/', views.add_fleet_customer, name='add_customer'),
    path('customers/<int:customer_id>/remove/', views.remove_fleet_customer, name='remove_customer'),
    path('generate/', views.invoice_generate, name='generate'),
    path('<int:invoice_id>/', views.invoice_detail, name='detail'),
    path('<int:invoice_id>/pay/', views.invoice_mark_paid, name='mark_paid'),
]
