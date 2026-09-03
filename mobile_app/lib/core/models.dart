class CompanyFeatures {
  final bool hasMobileBooking;
  final bool hasLoyalty;
  final bool hasMonthlyBilling;
  final bool hasInspections;
  final bool hasCommissions;
  final bool hasPushNotifications;

  CompanyFeatures({
    required this.hasMobileBooking,
    required this.hasLoyalty,
    required this.hasMonthlyBilling,
    required this.hasInspections,
    required this.hasCommissions,
    required this.hasPushNotifications,
  });

  factory CompanyFeatures.fromJson(Map<String, dynamic> json) {
    return CompanyFeatures(
      hasMobileBooking: json['has_mobile_booking'] ?? true,
      hasLoyalty: json['has_loyalty'] ?? false,
      hasMonthlyBilling: json['has_monthly_billing'] ?? false,
      hasInspections: json['has_inspections'] ?? false,
      hasCommissions: json['has_commissions'] ?? false,
      hasPushNotifications: json['has_push_notifications'] ?? false,
    );
  }
}

class Company {
  final int id;
  final String name;
  final String slug;
  final String phone;
  final String address;
  final String city;
  final String? logo;
  final String planCode;
  final String planName;
  final CompanyFeatures features;

  Company({
    required this.id,
    required this.name,
    required this.slug,
    required this.phone,
    required this.address,
    required this.city,
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
      address: json['address'] ?? '',
      city: json['city'] ?? '',
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
  final int loyaltyPoints;

  ServiceItem({
    required this.id,
    required this.name,
    required this.description,
    required this.price,
    required this.durationMinutes,
    required this.loyaltyPoints,
  });

  factory ServiceItem.fromJson(Map<String, dynamic> json) {
    return ServiceItem(
      id: json['id'],
      name: json['name'] ?? '',
      description: json['description'] ?? '',
      price: double.tryParse(json['default_price'].toString()) ?? 0.0,
      durationMinutes: json['estimated_duration_minutes'] ?? 45,
      loyaltyPoints: json['loyalty_points_earned'] ?? 10,
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

  VehicleItem({
    required this.id,
    required this.plate,
    required this.brand,
    required this.model,
    required this.color,
    required this.vehicleType,
  });

  factory VehicleItem.fromJson(Map<String, dynamic> json) {
    return VehicleItem(
      id: json['id'],
      plate: json['plate'] ?? '',
      brand: json['brand'] ?? '',
      model: json['model'] ?? '',
      color: json['color'] ?? '',
      vehicleType: json['vehicle_type'] ?? 'sedan',
    );
  }
}

class OrderPhotoItem {
  final int id;
  final String stage;
  final String imageUrl;
  final String caption;

  OrderPhotoItem({
    required this.id,
    required this.stage,
    required this.imageUrl,
    required this.caption,
  });

  factory OrderPhotoItem.fromJson(Map<String, dynamic> json) {
    return OrderPhotoItem(
      id: json['id'],
      stage: json['stage'] ?? 'before',
      imageUrl: json['image'] ?? '',
      caption: json['caption'] ?? '',
    );
  }
}

class ServiceOrderItem {
  final int id;
  final String companyName;
  final String vehiclePlate;
  final String serviceName;
  final double finalPrice;
  final String status;
  final List<OrderPhotoItem> photos;

  ServiceOrderItem({
    required this.id,
    required this.companyName,
    required this.vehiclePlate,
    required this.serviceName,
    required this.finalPrice,
    required this.status,
    required this.photos,
  });

  factory ServiceOrderItem.fromJson(Map<String, dynamic> json) {
    var photosList = (json['photos'] as List? ?? [])
        .map((p) => OrderPhotoItem.fromJson(p))
        .toList();

    return ServiceOrderItem(
      id: json['id'],
      companyName: json['company_name'] ?? '',
      vehiclePlate: json['vehicle_plate'] ?? '',
      serviceName: json['service_name'] ?? '',
      finalPrice: double.tryParse(json['final_price'].toString()) ?? 0.0,
      status: json['status'] ?? 'waiting',
      photos: photosList,
    );
  }

  String get statusLabel {
    switch (status) {
      case 'waiting':
        return 'Aguardando Início';
      case 'in_progress':
        return 'Em Lavagem / Estética';
      case 'completed':
        return 'Pronto para Retirada!';
      case 'delivered':
        return 'Entregue ao Motorista';
      default:
        return status;
    }
  }
}

class LoyaltyBalance {
  final int pointsBalance;
  final int totalEarned;
  final String rewardDescription;
  final int pointsNeeded;

  LoyaltyBalance({
    required this.pointsBalance,
    required this.totalEarned,
    required this.rewardDescription,
    required this.pointsNeeded,
  });

  factory LoyaltyBalance.fromJson(Map<String, dynamic> json) {
    return LoyaltyBalance(
      pointsBalance: json['points_balance'] ?? 0,
      totalEarned: json['total_points_earned'] ?? 0,
      rewardDescription: json['reward_description'] ?? 'Recompensa VIP',
      pointsNeeded: json['points_needed'] ?? 100,
    );
  }
}
