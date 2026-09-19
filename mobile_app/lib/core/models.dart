class CompanyFeatures {
  final bool hasMobileBooking;
  final bool hasLoyalty;
  final bool hasMonthlyBilling;
  final bool hasInspections;
  final bool hasCommissions;
  final bool hasPushNotifications;
  final bool hasCustomReports;

  CompanyFeatures({
    required this.hasMobileBooking,
    required this.hasLoyalty,
    required this.hasMonthlyBilling,
    required this.hasInspections,
    required this.hasCommissions,
    required this.hasPushNotifications,
    required this.hasCustomReports,
  });

  factory CompanyFeatures.fromJson(Map<String, dynamic> json) {
    return CompanyFeatures(
      hasMobileBooking: json['has_mobile_booking'] ?? true,
      hasLoyalty: json['has_loyalty'] ?? false,
      hasMonthlyBilling: json['has_monthly_billing'] ?? false,
      hasInspections: json['has_inspections'] ?? false,
      hasCommissions: json['has_commissions'] ?? false,
      hasPushNotifications: json['has_push_notifications'] ?? false,
      hasCustomReports: json['has_custom_reports'] ?? false,
    );
  }
}

class Company {
  final int id;
  final String name;
  final String slug;
  final String phone;
  final String email;
  final String address;
  final String city;
  final String state;
  final String? logo;
  final String planCode;
  final String planName;
  final CompanyFeatures features;

  Company({
    required this.id,
    required this.name,
    required this.slug,
    required this.phone,
    required this.email,
    required this.address,
    required this.city,
    required this.state,
    this.logo,
    required this.planCode,
    required this.planName,
    required this.features,
  });

  factory Company.fromJson(Map<String, dynamic> json) {
    return Company(
      id: json['id'],
      name: json['name'] ?? '',
      slug: json['slug'] ?? '',
      phone: json['phone'] ?? '',
      email: json['email'] ?? '',
      address: json['address'] ?? '',
      city: json['city'] ?? '',
      state: json['state'] ?? '',
      logo: json['logo'],
      planCode: json['plan_code'] ?? 'basic',
      planName: json['plan_name'] ?? 'Básico',
      features: CompanyFeatures.fromJson(json['features'] ?? {}),
    );
  }
}

class ServiceItem {
  final int id;
  final String name;
  final String description;
  final double price;
  final int durationMinutes;
  final bool countsForLoyalty;
  final int loyaltyPoints;
  final String categoryName;

  ServiceItem({
    required this.id,
    required this.name,
    required this.description,
    required this.price,
    required this.durationMinutes,
    required this.countsForLoyalty,
    required this.loyaltyPoints,
    required this.categoryName,
  });

  factory ServiceItem.fromJson(Map<String, dynamic> json) {
    return ServiceItem(
      id: json['id'],
      name: json['name'] ?? '',
      description: json['description'] ?? '',
      price: double.tryParse(json['default_price'].toString()) ?? 0.0,
      durationMinutes: json['estimated_duration_minutes'] ?? 45,
      countsForLoyalty: json['counts_for_loyalty'] ?? true,
      loyaltyPoints: json['loyalty_points_earned'] ?? 10,
      categoryName: json['category_name'] ?? 'Estética Automotiva',
    );
  }
}

class VehicleItem {
  final int id;
  final String plate;
  final String brand;
  final String model;
  final String color;
  final String vehicleType;
  final String? photo;

  VehicleItem({
    required this.id,
    required this.plate,
    required this.brand,
    required this.model,
    required this.color,
    required this.vehicleType,
    this.photo,
  });

  factory VehicleItem.fromJson(Map<String, dynamic> json) {
    return VehicleItem(
      id: json['id'],
      plate: json['plate'] ?? '',
      brand: json['brand'] ?? '',
      model: json['model'] ?? '',
      color: json['color'] ?? '',
      vehicleType: json['vehicle_type'] ?? 'sedan',
      photo: json['photo'],
    );
  }
}

class OrderPhotoItem {
  final int id;
  final String stage;
  final String imageUrl;
  final String caption;
  final String? createdAt;

  OrderPhotoItem({
    required this.id,
    required this.stage,
    required this.imageUrl,
    required this.caption,
    this.createdAt,
  });

  factory OrderPhotoItem.fromJson(Map<String, dynamic> json) {
    return OrderPhotoItem(
      id: json['id'],
      stage: json['stage'] ?? 'before',
      imageUrl: json['image'] ?? '',
      caption: json['caption'] ?? '',
      createdAt: json['created_at'],
    );
  }
}

class ServiceOrderItem {
  final int id;
  final String companyName;
  final String companyAddress;
  final String vehiclePlate;
  final String vehicleBrand;
  final String vehicleModel;
  final String serviceName;
  final double price;
  final double discount;
  final double finalPrice;
  final String status;
  final String paymentMethod;
  final String? startedAt;
  final String? completedAt;
  final String? deliveredAt;
  final List<OrderPhotoItem> photos;
  final String? createdAt;

  ServiceOrderItem({
    required this.id,
    required this.companyName,
    required this.companyAddress,
    required this.vehiclePlate,
    required this.vehicleBrand,
    required this.vehicleModel,
    required this.serviceName,
    required this.price,
    required this.discount,
    required this.finalPrice,
    required this.status,
    required this.paymentMethod,
    this.startedAt,
    this.completedAt,
    this.deliveredAt,
    required this.photos,
    this.createdAt,
  });

  factory ServiceOrderItem.fromJson(Map<String, dynamic> json) {
    var photosList = (json['photos'] as List? ?? [])
        .map((p) => OrderPhotoItem.fromJson(p))
        .toList();

    return ServiceOrderItem(
      id: json['id'],
      companyName: json['company_name'] ?? '',
      companyAddress: json['company_address'] ?? '',
      vehiclePlate: json['vehicle_plate'] ?? '',
      vehicleBrand: json['vehicle_brand'] ?? '',
      vehicleModel: json['vehicle_model'] ?? '',
      serviceName: json['service_name'] ?? '',
      price: double.tryParse(json['price'].toString()) ?? 0.0,
      discount: double.tryParse(json['discount'].toString()) ?? 0.0,
      finalPrice: double.tryParse(json['final_price'].toString()) ?? 0.0,
      status: json['status'] ?? 'waiting',
      paymentMethod: json['payment_method'] ?? 'cash',
      startedAt: json['started_at'],
      completedAt: json['completed_at'],
      deliveredAt: json['delivered_at'],
      photos: photosList,
      createdAt: json['created_at'],
    );
  }

  String get statusLabel {
    switch (status) {
      case 'waiting':
        return 'Na Fila';
      case 'in_progress':
      case 'washing':
        return 'Em Atendimento';
      case 'completed':
        return 'Pronto para Retirada';
      case 'delivered':
        return 'Entregue ao Motorista';
      case 'cancelled':
        return 'Cancelado';
      default:
        return status;
    }
  }

  int get currentStep {
    switch (status) {
      case 'waiting':
        return 1;
      case 'in_progress':
      case 'washing':
        return 2;
      case 'completed':
        return 3;
      case 'delivered':
        return 4;
      default:
        return 1;
    }
  }
}

class AppointmentItem {
  final int id;
  final int companyId;
  final String companyName;
  final String companyAddress;
  final int? vehicleId;
  final String vehiclePlate;
  final String vehicleBrand;
  final String vehicleModel;
  final int? serviceTypeId;
  final String serviceName;
  final String scheduledDate;
  final String scheduledTime;
  final String status;
  final String notes;

  AppointmentItem({
    required this.id,
    required this.companyId,
    required this.companyName,
    required this.companyAddress,
    this.vehicleId,
    required this.vehiclePlate,
    required this.vehicleBrand,
    required this.vehicleModel,
    this.serviceTypeId,
    required this.serviceName,
    required this.scheduledDate,
    required this.scheduledTime,
    required this.status,
    required this.notes,
  });

  factory AppointmentItem.fromJson(Map<String, dynamic> json) {
    return AppointmentItem(
      id: json['id'],
      companyId: json['company'] is int ? json['company'] : (json['company']?['id'] ?? 0),
      companyName: json['company_name'] ?? '',
      companyAddress: json['company_address'] ?? '',
      vehicleId: json['vehicle'] is int ? json['vehicle'] : (json['vehicle']?['id']),
      vehiclePlate: json['vehicle_plate'] ?? '',
      vehicleBrand: json['vehicle_brand'] ?? '',
      vehicleModel: json['vehicle_model'] ?? '',
      serviceTypeId: json['service_type'] is int ? json['service_type'] : (json['service_type']?['id']),
      serviceName: json['service_name'] ?? '',
      scheduledDate: json['scheduled_date'] ?? '',
      scheduledTime: json['scheduled_time'] ?? '',
      status: json['status'] ?? 'pending',
      notes: json['notes'] ?? '',
    );
  }

  String get statusLabel {
    switch (status) {
      case 'pending':
        return 'Pendente';
      case 'confirmed':
        return 'Confirmado';
      case 'arrived':
        return 'No Local';
      case 'completed':
        return 'Finalizado';
      case 'cancelled':
        return 'Cancelado';
      default:
        return status;
    }
  }

  bool get canCancel => status == 'pending' || status == 'confirmed';
}

class LoyaltyEventItem {
  final int id;
  final String eventType;
  final int points;
  final String description;
  final String createdAt;

  LoyaltyEventItem({
    required this.id,
    required this.eventType,
    required this.points,
    required this.description,
    required this.createdAt,
  });

  factory LoyaltyEventItem.fromJson(Map<String, dynamic> json) {
    return LoyaltyEventItem(
      id: json['id'] ?? 0,
      eventType: json['event_type'] ?? 'earned',
      points: json['points'] ?? 0,
      description: json['description'] ?? '',
      createdAt: json['created_at'] ?? '',
    );
  }
}

class LoyaltyAccountItem {
  final int companyId;
  final String companyName;
  final String companyCity;
  final String? companyLogo;
  final int pointsBalance;
  final int totalPointsEarned;
  final int totalRewardsRedeemed;
  final String rewardDescription;
  final int pointsNeeded;
  final List<LoyaltyEventItem> events;

  LoyaltyAccountItem({
    required this.companyId,
    required this.companyName,
    required this.companyCity,
    this.companyLogo,
    required this.pointsBalance,
    required this.totalPointsEarned,
    required this.totalRewardsRedeemed,
    required this.rewardDescription,
    required this.pointsNeeded,
    required this.events,
  });

  factory LoyaltyAccountItem.fromJson(Map<String, dynamic> json) {
    var eventsList = (json['events'] as List? ?? [])
        .map((e) => LoyaltyEventItem.fromJson(e))
        .toList();

    return LoyaltyAccountItem(
      companyId: json['company_id'] ?? 0,
      companyName: json['company_name'] ?? '',
      companyCity: json['company_city'] ?? '',
      companyLogo: json['company_logo'],
      pointsBalance: json['points_balance'] ?? 0,
      totalPointsEarned: json['total_points_earned'] ?? 0,
      totalRewardsRedeemed: json['total_rewards_redeemed'] ?? 0,
      rewardDescription: json['reward_description'] ?? 'Recompensa VIP',
      pointsNeeded: json['points_needed'] ?? 100,
      events: eventsList,
    );
  }

  double get progressPercentage {
    if (pointsNeeded <= 0) return 0.0;
    return (pointsBalance / pointsNeeded).clamp(0.0, 1.0);
  }
}
