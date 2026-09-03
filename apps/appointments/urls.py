from django.urls import path
from apps.appointments import views

urlpatterns = [
    path('', views.appointment_list, name='list'),
    path('<int:appointment_id>/check-in/', views.check_in_appointment, name='check_in'),
    path('<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel'),
]
