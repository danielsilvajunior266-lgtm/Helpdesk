from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.accounts.models import User
from apps.saas_core.models import Company
from apps.customers.models import Customer, Vehicle
from apps.services.models import ServiceType
from apps.orders.models import ServiceOrder, OrderPhoto
from apps.appointments.models import Appointment
from apps.loyalty.models import LoyaltyAccount, LoyaltyEvent

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'] = serializers.CharField(required=False)
        self.fields['email'] = serializers.CharField(required=False)

    def validate(self, attrs):
        login_val = (attrs.get('email') or attrs.get('username') or '').strip()
        password = (attrs.get('password') or '').strip()

        if not login_val:
            raise serializers.ValidationError({'detail': 'Informe seu e-mail ou nome de usuário.'})

        user = User.objects.filter(email__iexact=login_val).first()
        if not user:
            user = User.objects.filter(username__iexact=login_val).first()

        if user and user.check_password(password):
            if not user.is_active:
                raise serializers.ValidationError({'detail': 'Esta conta de usuário está desativada.'})
            refresh = self.get_token(user)
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'name': user.get_full_name() or user.username,
                    'email': user.email,
                    'role': user.role,
                }
            }
        raise serializers.ValidationError({'detail': 'E-mail/Usuário ou senha incorretos. Verifique suas credenciais.'})


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
        request = self.context.get('request')
        user = request.user if request else None
        company = self.context.get('company') or (user.company if user else None)

        if not company and request:
            company_id = request.data.get('company') or request.data.get('company_id')
            if company_id and str(company_id).isdigit():
                company = Company.objects.filter(id=int(company_id), status='active').first()

        if not company:
            company = Company.objects.filter(status='active').first()

        if not company:
            raise serializers.ValidationError({'company': 'Nenhuma empresa operacional encontrada para associar o veículo.'})

        # Obtém ou cria o perfil de Customer para o usuário autenticado de forma segura
        customer = Customer.objects.filter(user=user, company=company).first()
        if not customer:
            customer = Customer.objects.create(
                user=user,
                company=company,
                name=user.get_full_name() or user.username,
                phone=user.phone or '0000000000',
                email=user.email or '',
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
            password=password,
            **validated_data
        )
        return user


class AppointmentSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service_type.name', read_only=True)
    vehicle_plate = serializers.CharField(source='vehicle.plate', read_only=True)
    vehicle_brand = serializers.CharField(source='vehicle.brand', default='', read_only=True)
    vehicle_model = serializers.CharField(source='vehicle.model', default='', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_address = serializers.CharField(source='company.address', default='', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'company', 'company_name', 'company_address', 'vehicle', 'vehicle_plate',
            'vehicle_brand', 'vehicle_model', 'service_type', 'service_name',
            'scheduled_date', 'scheduled_time', 'status', 'notes'
        ]
        read_only_fields = ['status', 'company_name', 'company_address', 'vehicle_plate', 'vehicle_brand', 'vehicle_model', 'service_name']

    def validate(self, attrs):
        request = self.context.get('request')
        company = attrs.get('company')
        service_type = attrs.get('service_type')
        vehicle = attrs.get('vehicle')

        # 1. Valida se a empresa possui a funcionalidade de agendamento online ativa no plano
        if company and not company.has_feature('mobile_booking'):
            raise serializers.ValidationError(
                {'company': f'A empresa "{company.name}" não aceita agendamentos pelo aplicativo no plano atual.'}
            )

        # 2. Valida se o serviço pertence à empresa informada
        if service_type and company and service_type.company_id != company.id:
            raise serializers.ValidationError(
                {'service_type': f'O serviço selecionado não pertence ao catálogo de {company.name}.'}
            )

        # 3. Valida se o veículo pertence ao usuário autenticado
        if request and request.user.is_authenticated and vehicle:
            if not Vehicle.objects.filter(id=vehicle.id, customer__user=request.user).exists():
                raise serializers.ValidationError(
                    {'vehicle': 'O veículo selecionado não pertence à sua garagem.'}
                )

        return attrs


class OrderPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderPhoto
        fields = ['id', 'stage', 'image', 'caption', 'created_at']


class ServiceOrderSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service_type.name', read_only=True)
    vehicle_plate = serializers.CharField(source='vehicle.plate', read_only=True)
    vehicle_brand = serializers.CharField(source='vehicle.brand', default='', read_only=True)
    vehicle_model = serializers.CharField(source='vehicle.model', default='', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_address = serializers.CharField(source='company.address', default='', read_only=True)
    photos = OrderPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = ServiceOrder
        fields = [
            'id', 'company_name', 'company_address', 'vehicle_plate', 'vehicle_brand',
            'vehicle_model', 'service_name', 'price', 'discount', 'final_price',
            'status', 'payment_method', 'started_at', 'completed_at', 'delivered_at',
            'photos', 'created_at'
        ]


class LoyaltyEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyEvent
        fields = ['id', 'event_type', 'points', 'description', 'created_at']


class LoyaltyAccountSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(source='company.id', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_slug = serializers.CharField(source='company.slug', read_only=True)
    company_city = serializers.CharField(source='company.city', default='', read_only=True)
    company_logo = serializers.SerializerMethodField()
    events = LoyaltyEventSerializer(many=True, read_only=True)
    reward_description = serializers.CharField(source='company.loyalty_loyaltyprogram_set.first.reward_name', default='Recompensa VIP', read_only=True)
    points_needed = serializers.IntegerField(source='company.loyalty_loyaltyprogram_set.first.points_needed_for_reward', default=100, read_only=True)

    class Meta:
        model = LoyaltyAccount
        fields = [
            'company_id', 'company_name', 'company_slug', 'company_city', 'company_logo',
            'points_balance', 'total_points_earned', 'total_rewards_redeemed',
            'reward_description', 'points_needed', 'events'
        ]

    def get_company_logo(self, obj):
        if obj.company and obj.company.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.company.logo.url)
            return obj.company.logo.url
        return None
