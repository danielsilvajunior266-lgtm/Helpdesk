from django.urls import path
from apps.commissions import views

urlpatterns = [
    path('', views.commission_list, name='list'),
    path('<int:commission_id>/pay/', views.commission_pay, name='pay'),
]
