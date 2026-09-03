from django.urls import path
from apps.services import views

urlpatterns = [
    path('', views.service_list, name='list'),
    path('new/', views.service_create, name='create'),
]
