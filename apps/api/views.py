from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from apps.saas_core.models import Company
from apps.customers.models import Customer, Vehicle
from apps.services.models import ServiceType
from apps.orders.models import ServiceOrder
from apps.appointments.models import Appointment
from apps.loyalty.models import LoyaltyAccount
from apps.api.serializers import (
    CompanySerializer,
    ServiceTypeSerializer,
    VehicleSerializer,
    RegisterCustomerSerializer,
    AppointmentSerializer,
    ServiceOrderSerializer,
    LoyaltyAccountSerializer
)

class RegisterCustomerAPIView(generics.CreateAPIView):
    serializer_class = RegisterCustomerSerializer
    permission_classes = [permissions.AllowAny]


class CompanyListAPIView(generics.ListAPIView):
    serializer_class = CompanySerializer
    permission_classes = [permissions.AllowAny]
    queryset = Company.objects.filter(status='active').select_related('plan')


class CompanyDetailAPIView(generics.RetrieveAPIView):
    serializer_class = CompanySerializer
    permission_classes = [permissions.AllowAny]
    queryset = Company.objects.filter(status='active').select_related('plan')


class CompanyServicesListAPIView(generics.ListAPIView):
    serializer_class = ServiceTypeSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        company_id = self.kwargs['company_id']
        return ServiceType.objects.filter(company_id=company_id, is_active=True).select_related('category')


class CustomerVehicleListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Vehicle.objects.filter(customer__user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Se passado X-Company-ID ou company_id na query/header
        company_id = self.request.headers.get('X-Company-ID') or self.request.query_params.get('company_id')
        if company_id and str(company_id).isdigit():
            context['company'] = Company.objects.filter(id=int(company_id)).first()
        return context


class CustomerAppointmentsListAPIView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(customer__user=self.request.user).select_related(
            'company', 'vehicle', 'service_type'
        )


class AppointmentCreateAPIView(generics.CreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        company = serializer.validated_data['company']
        customer, _ = Customer.objects.get_or_create(
            user=user,
            company=company,
            defaults={
                'name': user.get_full_name() or user.username,
                'phone': user.phone or '0000000000',
                'email': user.email
            }
        )
        serializer.save(customer=customer)


class CustomerOrdersListAPIView(generics.ListAPIView):
    serializer_class = ServiceOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ServiceOrder.objects.filter(
            customer__user=self.request.user
        ).select_related('company', 'vehicle', 'service_type').prefetch_related('photos')


class CustomerLoyaltyBalanceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        company_id = request.query_params.get('company_id') or request.headers.get('X-Company-ID')
        if not company_id:
            return Response({'error': 'company_id_required', 'detail': 'Informe a empresa via query param ?company_id= ou header X-Company-ID.'}, status=status.HTTP_400_BAD_REQUEST)

        account = LoyaltyAccount.objects.filter(
            customer__user=request.user,
            company_id=company_id
        ).prefetch_related('events').first()

        if not account:
            return Response({
                'points_balance': 0,
                'total_points_earned': 0,
                'total_rewards_redeemed': 0,
                'reward_description': 'Recompensa VIP',
                'points_needed': 100,
                'events': []
            })

        serializer = LoyaltyAccountSerializer(account)
        return Response(serializer.data)
