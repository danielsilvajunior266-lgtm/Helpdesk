from django.urls import path
from apps.employees import views

app_name = 'employees'

urlpatterns = [
    path('', views.employee_dashboard, name='dashboard'),
    
    # Ajudantes Diários
    path('helpers/new/', views.daily_helper_create, name='daily_helper_create'),
    path('helpers/<int:helper_id>/edit/', views.daily_helper_edit, name='daily_helper_edit'),
    path('works/new/', views.daily_work_create, name='daily_work_create'),
    path('works/<int:work_id>/pay/', views.daily_work_pay, name='daily_work_pay'),

    # Funcionários Registrados
    path('registered/new/', views.registered_employee_create, name='registered_employee_create'),
    path('registered/<int:employee_id>/edit/', views.registered_employee_edit, name='registered_employee_edit'),
    path('registered/<int:employee_id>/toggle-status/', views.registered_employee_toggle_status, name='registered_employee_toggle_status'),
    path('registered/<int:employee_id>/pay-salary/', views.salary_payment_create, name='salary_payment_create'),
]
