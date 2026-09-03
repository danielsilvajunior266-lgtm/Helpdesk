from django.urls import path
from apps.customers import views

urlpatterns = [
    path('', views.customer_list, name='list'),
    path('new/', views.customer_create, name='create'),
    path('<int:customer_id>/vehicles/new/', views.vehicle_create, name='vehicle_create'),
]
