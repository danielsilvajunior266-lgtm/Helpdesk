from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.api import views

urlpatterns = [
    # Autenticação JWT do Cliente Motorista
    path('auth/register/', views.RegisterCustomerAPIView.as_view(), name='register_customer'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Descoberta de Lava-jatos e Catálogos
    path('companies/', views.CompanyListAPIView.as_view(), name='companies_list'),
    path('companies/<int:pk>/', views.CompanyDetailAPIView.as_view(), name='company_detail'),
    path('companies/<int:company_id>/services/', views.CompanyServicesListAPIView.as_view(), name='company_services'),

    # Garagem Digital (Veículos do Cliente)
    path('vehicles/', views.CustomerVehicleListCreateAPIView.as_view(), name='customer_vehicles'),

    # Agendamentos Online
    path('appointments/', views.CustomerAppointmentsListAPIView.as_view(), name='customer_appointments'),
    path('appointments/book/', views.AppointmentCreateAPIView.as_view(), name='book_appointment'),

    # Acompanhamento em Tempo Real & Fotos Antes/Depois
    path('orders/', views.CustomerOrdersListAPIView.as_view(), name='customer_orders'),

    # Clube de Fidelidade
    path('loyalty/', views.CustomerLoyaltyBalanceAPIView.as_view(), name='customer_loyalty'),
]
