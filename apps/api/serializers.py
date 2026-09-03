from rest_framework import serializers
from apps.accounts.models import User
from apps.saas_core.models import Company
from apps.customers.models import Customer, Vehicle
from apps.services.models import ServiceType
from apps.orders.models import ServiceOrder, OrderPhoto
from apps.appointments.models import Appointment
from apps.loyalty.models import LoyaltyAccount, LoyaltyEvent

class CompanySerializer(serializers.ModelSerializer):
    plan_code = serializers.CharField(source='plan.code', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    features = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'phone', 'email', 'address', 'city', 'state',
            'latitude', 'longitude', 'logo', 'plan_code', 'plan_name', 'features'
        ]

    def get_features(self, obj):
        return {
            'has_mobile_booking': obj.has_feature('mobile_booking'),
            'has_loyalty': obj.has_feature('loyalty'),
            'has_monthly_billing': obj.has_feature('monthly_billing'),
            'has_inspections': obj.has_feature('inspections'),
            'has_commissions': obj.has_feature('commissions'),
            'has_push_notifications': obj.has_feature('push_notifications'),
            'has_custom_reports': obj.has_feature('custom_reports'),
        }


class ServiceTypeSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = ServiceType
        fields = [
            'id', 'name', 'description', 'default_price', 'estimated_duration_minutes',
            'counts_for_loyalty', 'loyalty_points_earned', 'category_name'
        ]


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'plate', 'brand', 'model', 'color', 'vehicle_type', 'photo']

    def create(self, validated_data):
        user = self.context['request'].user
        company = self.context.get('company') or user.company
        
        # Obtém ou cria o perfil de Customer para o usuário autenticado
        customer, _ = Customer.objects.get_or_create(
            user=user,
            company=company,
            defaults={
                'name': user.get_full_name() or user.username,
                'phone': user.phone or '0000000000',
                'email': user.email,
            }
        )
        return Vehicle.objects.create(company=company, customer=customer, **validated_data)


class RegisterCustomerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'phone']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(
            role='customer',
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user


class AppointmentSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service_type.name', read_only=True)
    vehicle_plate = serializers.CharField(source='vehicle.plate', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'company', 'company_name', 'vehicle', 'vehicle_plate',
            'service_type', 'service_name', 'scheduled_date', 'scheduled_time',
            'status', 'notes'
        ]
        read_only_fields = ['status', 'company_name', 'vehicle_plate', 'service_name']


class OrderPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderPhoto
        fields = ['id', 'stage', 'image', 'caption', 'created_at']


class ServiceOrderSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service_type.name', read_only=True)
    vehicle_plate = serializers.CharField(source='vehicle.plate', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    photos = OrderPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = ServiceOrder
        fields = [
            'id', 'company_name', 'vehicle_plate', 'service_name',
            'price', 'discount', 'final_price', 'status', 'payment_method',
            'started_at', 'completed_at', 'delivered_at', 'photos', 'created_at'
        ]


class LoyaltyEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyEvent
        fields = ['id', 'event_type', 'points', 'description', 'created_at']


class LoyaltyAccountSerializer(serializers.ModelSerializer):
    events = LoyaltyEventSerializer(many=True, read_only=True)
    reward_description = serializers.CharField(source='company.saas_core_loyaltyprogram_set.first.reward_description', default='Recompensa VIP', read_only=True)
    points_needed = serializers.IntegerField(source='company.saas_core_loyaltyprogram_set.first.points_needed_for_reward', default=100, read_only=True)

    class Meta:
        model = LoyaltyAccount
        fields = ['points_balance', 'total_points_earned', 'total_rewards_redeemed', 'reward_description', 'points_needed', 'events']
