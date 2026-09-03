from django.urls import path
from apps.portal import views

app_name = 'portal'

urlpatterns = [
    path('', views.portal_home, name='home'),
    path('select/', views.portal_select_company, name='select_company'),
    path('switch/<int:company_id>/', views.portal_switch_company, name='switch_company'),
    path('book/', views.portal_book_appointment, name='book_appointment'),
    path('garage/add/', views.portal_add_vehicle, name='add_vehicle'),
    path('garage/delete/<int:vehicle_id>/', views.portal_delete_vehicle, name='delete_vehicle'),
    path('appointment/cancel/<int:appointment_id>/', views.portal_cancel_appointment, name='cancel_appointment'),
]
