import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'api_config.dart';
import 'models.dart';

class AuthResult {
  final bool success;
  final String? message;
  AuthResult({required this.success, this.message});
}

class _CacheEntry<T> {
  final T data;
  final DateTime timestamp;
  _CacheEntry(this.data) : timestamp = DateTime.now();

  bool isValid(Duration ttl) => DateTime.now().difference(timestamp) < ttl;
}

class ApiService {
  // In-memory cache map for high performance
  static final Map<String, _CacheEntry<dynamic>> _cache = {};

  static void invalidateCache([String? keyPrefix]) {
    if (keyPrefix == null) {
      _cache.clear();
    } else {
      _cache.removeWhere((k, _) => k.startsWith(keyPrefix));
    }
  }

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  static Future<String?> getUserDisplayName() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('user_display_name');
  }

  static Future<http.Response> _get(String path, {Map<String, String>? headers}) async {
    try {
      return await http.get(
        Uri.parse('${ApiConfig.baseUrl}$path'),
        headers: headers,
      ).timeout(const Duration(seconds: 4));
    } catch (_) {
      return await http.get(
        Uri.parse('${ApiConfig.fallbackUrl}$path'),
        headers: headers,
      ).timeout(const Duration(seconds: 6));
    }
  }

  static Future<http.Response> _post(String path, Map<String, dynamic> body, {Map<String, String>? headers}) async {
    headers ??= {'Content-Type': 'application/json'};
    final encoded = jsonEncode(body);
    try {
      return await http.post(
        Uri.parse('${ApiConfig.baseUrl}$path'),
        headers: headers,
        body: encoded,
      ).timeout(const Duration(seconds: 4));
    } catch (_) {
      return await http.post(
        Uri.parse('${ApiConfig.fallbackUrl}$path'),
        headers: headers,
        body: encoded,
      ).timeout(const Duration(seconds: 6));
    }
  }

  static Future<http.Response> _delete(String path, {Map<String, String>? headers}) async {
    try {
      return await http.delete(
        Uri.parse('${ApiConfig.baseUrl}$path'),
        headers: headers,
      ).timeout(const Duration(seconds: 4));
    } catch (_) {
      return await http.delete(
        Uri.parse('${ApiConfig.fallbackUrl}$path'),
        headers: headers,
      ).timeout(const Duration(seconds: 6));
    }
  }

  static Future<AuthResult> login(String emailOrUsername, String password) async {
    if (emailOrUsername.trim().isEmpty || password.trim().isEmpty) {
      return AuthResult(success: false, message: 'Informe o e-mail/usuário e a senha.');
    }

    try {
      final response = await _post(
        '/auth/login/',
        {
          'email': emailOrUsername.trim(),
          'username': emailOrUsername.trim(),
          'password': password.trim(),
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('access_token', data['access']);
        String displayName = emailOrUsername.contains('@') ? emailOrUsername.split('@').first : emailOrUsername;
        if (data['user'] != null && data['user']['name'] != null && data['user']['name'].toString().isNotEmpty) {
          displayName = data['user']['name'];
        }
        await prefs.setString('user_display_name', displayName);
        invalidateCache(); // Invalida cache ao autenticar novo usuário
        return AuthResult(success: true);
      } else {
        try {
          final err = jsonDecode(utf8.decode(response.bodyBytes));
          final msg = err['detail'] ?? err['error'] ?? 'E-mail ou senha incorretos.';
          return AuthResult(success: false, message: msg.toString());
        } catch (_) {
          return AuthResult(success: false, message: 'Falha no login (Status: ${response.statusCode})');
        }
      }
    } catch (e) {
      return AuthResult(success: false, message: 'Não foi possível conectar ao servidor. Verifique a conexão.');
    }
  }

  static Future<AuthResult> register({
    required String firstName,
    required String lastName,
    required String phone,
    required String email,
    required String password,
  }) async {
    if (firstName.trim().isEmpty || phone.trim().isEmpty || email.trim().isEmpty || password.trim().isEmpty) {
      return AuthResult(success: false, message: 'Preencha todos os campos obrigatórios.');
    }

    try {
      final response = await _post(
        '/auth/register/',
        {
          'first_name': firstName.trim(),
          'last_name': lastName.trim(),
          'phone': phone.trim(),
          'email': email.trim(),
          'password': password.trim(),
        },
      );

      if (response.statusCode == 201) {
        return await login(email, password);
      } else {
        try {
          final err = jsonDecode(utf8.decode(response.bodyBytes));
          final msg = err['detail'] ?? err['error'] ?? err.toString();
          return AuthResult(success: false, message: msg.toString());
        } catch (_) {
          return AuthResult(success: false, message: 'Erro ao cadastrar (Status: ${response.statusCode})');
        }
      }
    } catch (_) {
      return AuthResult(success: false, message: 'Não foi possível conectar ao servidor para cadastro.');
    }
  }

  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    await prefs.remove('user_display_name');
    invalidateCache();
  }

  static Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  static Future<List<Company>> getCompanies({String query = '', bool forceRefresh = false}) async {
    final cacheKey = 'companies_$query';
    if (!forceRefresh && _cache.containsKey(cacheKey) && _cache[cacheKey]!.isValid(const Duration(minutes: 2))) {
      return _cache[cacheKey]!.data as List<Company>;
    }

    var path = '/companies/';
    if (query.isNotEmpty) {
      path += '?q=${Uri.encodeComponent(query)}';
    }
    try {
      final response = await _get(path);
      if (response.statusCode == 200) {
        final List data = jsonDecode(utf8.decode(response.bodyBytes));
        final list = data.map((item) => Company.fromJson(item)).toList();
        _cache[cacheKey] = _CacheEntry<List<Company>>(list);
        return list;
      }
    } catch (_) {}
    return _cache.containsKey(cacheKey) ? (_cache[cacheKey]!.data as List<Company>) : [];
  }

  static Future<Company?> getCompany(int id, {bool forceRefresh = false}) async {
    final cacheKey = 'company_$id';
    if (!forceRefresh && _cache.containsKey(cacheKey) && _cache[cacheKey]!.isValid(const Duration(minutes: 2))) {
      return _cache[cacheKey]!.data as Company;
    }

    try {
      final response = await _get('/companies/$id/');
      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        final company = Company.fromJson(data);
        _cache[cacheKey] = _CacheEntry<Company>(company);
        return company;
      }
    } catch (_) {}
    return _cache.containsKey(cacheKey) ? (_cache[cacheKey]!.data as Company) : null;
  }

  static Future<List<ServiceItem>> getServices(int companyId, {bool forceRefresh = false}) async {
    final cacheKey = 'services_$companyId';
    if (!forceRefresh && _cache.containsKey(cacheKey) && _cache[cacheKey]!.isValid(const Duration(minutes: 2))) {
      return _cache[cacheKey]!.data as List<ServiceItem>;
    }

    try {
      final response = await _get('/companies/$companyId/services/');
      if (response.statusCode == 200) {
        final List data = jsonDecode(utf8.decode(response.bodyBytes));
        final list = data.map((item) => ServiceItem.fromJson(item)).toList();
        _cache[cacheKey] = _CacheEntry<List<ServiceItem>>(list);
        return list;
      }
    } catch (_) {}
    return _cache.containsKey(cacheKey) ? (_cache[cacheKey]!.data as List<ServiceItem>) : [];
  }

  static Future<List<VehicleItem>> getMyVehicles({bool forceRefresh = false}) async {
    final token = await getToken();
    if (token == null || token.isEmpty) return [];

    const cacheKey = 'my_vehicles';
    if (!forceRefresh && _cache.containsKey(cacheKey) && _cache[cacheKey]!.isValid(const Duration(seconds: 30))) {
      return _cache[cacheKey]!.data as List<VehicleItem>;
    }

    try {
      final response = await _get(
        '/vehicles/',
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final List data = jsonDecode(utf8.decode(response.bodyBytes));
        final list = data.map((item) => VehicleItem.fromJson(item)).toList();
        _cache[cacheKey] = _CacheEntry<List<VehicleItem>>(list);
        return list;
      }
    } catch (_) {}
    return _cache.containsKey(cacheKey) ? (_cache[cacheKey]!.data as List<VehicleItem>) : [];
  }

  static Future<bool> createVehicle({
    int? companyId,
    required String plate,
    required String brand,
    required String model,
    required String color,
    String vehicleType = 'sedan',
  }) async {
    final token = await getToken();
    if (token == null || token.isEmpty) return false;

    try {
      final Map<String, dynamic> bodyData = {
        'plate': plate.toUpperCase().trim(),
        'brand': brand.trim(),
        'model': model.trim(),
        'color': color.trim(),
        'vehicle_type': vehicleType,
      };
      if (companyId != null) {
        bodyData['company'] = companyId;
      }

      final response = await _post(
        '/vehicles/',
        bodyData,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      final success = response.statusCode == 201 || response.statusCode == 200;
      if (success) {
        invalidateCache('my_vehicles');
      }
      return success;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> deleteVehicle(int vehicleId) async {
    final token = await getToken();
    if (token == null || token.isEmpty) return false;

    try {
      final response = await _delete(
        '/vehicles/$vehicleId/',
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      final success = response.statusCode == 204 || response.statusCode == 200;
      if (success) {
        invalidateCache('my_vehicles');
      }
      return success;
    } catch (_) {
      return false;
    }
  }

  static Future<List<ServiceOrderItem>> getMyOrders({bool forceRefresh = false}) async {
    final token = await getToken();
    if (token == null || token.isEmpty) return [];

    const cacheKey = 'my_orders';
    if (!forceRefresh && _cache.containsKey(cacheKey) && _cache[cacheKey]!.isValid(const Duration(seconds: 15))) {
      return _cache[cacheKey]!.data as List<ServiceOrderItem>;
    }

    try {
      final response = await _get(
        '/orders/',
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final List data = jsonDecode(utf8.decode(response.bodyBytes));
        final list = data.map((item) => ServiceOrderItem.fromJson(item)).toList();
        _cache[cacheKey] = _CacheEntry<List<ServiceOrderItem>>(list);
        return list;
      }
    } catch (_) {}
    return _cache.containsKey(cacheKey) ? (_cache[cacheKey]!.data as List<ServiceOrderItem>) : [];
  }

  static Future<List<AppointmentItem>> getAppointments({bool forceRefresh = false}) async {
    final token = await getToken();
    if (token == null || token.isEmpty) return [];

    const cacheKey = 'appointments';
    if (!forceRefresh && _cache.containsKey(cacheKey) && _cache[cacheKey]!.isValid(const Duration(seconds: 20))) {
      return _cache[cacheKey]!.data as List<AppointmentItem>;
    }

    try {
      final response = await _get(
        '/appointments/',
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final List data = jsonDecode(utf8.decode(response.bodyBytes));
        final list = data.map((item) => AppointmentItem.fromJson(item)).toList();
        _cache[cacheKey] = _CacheEntry<List<AppointmentItem>>(list);
        return list;
      }
    } catch (_) {}
    return _cache.containsKey(cacheKey) ? (_cache[cacheKey]!.data as List<AppointmentItem>) : [];
  }

  static Future<bool> bookAppointment({
    required int companyId,
    required int vehicleId,
    required int serviceTypeId,
    required String date,
    required String time,
    String notes = '',
  }) async {
    final token = await getToken();
    if (token == null || token.isEmpty) return false;

    try {
      final response = await _post(
        '/appointments/book/',
        {
          'company': companyId,
          'vehicle': vehicleId,
          'service_type': serviceTypeId,
          'scheduled_date': date,
          'scheduled_time': time,
          'notes': notes,
        },
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      final success = response.statusCode == 201;
      if (success) {
        invalidateCache('appointments');
        invalidateCache('my_orders');
      }
      return success;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> cancelAppointment(int appointmentId) async {
    final token = await getToken();
    if (token == null || token.isEmpty) return false;

    try {
      final response = await _post(
        '/appointments/$appointmentId/cancel/',
        {},
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      final success = response.statusCode == 200;
      if (success) {
        invalidateCache('appointments');
      }
      return success;
    } catch (_) {
      return false;
    }
  }

  static Future<LoyaltyAccountItem?> getLoyaltyBalance(int companyId, {bool forceRefresh = false}) async {
    final token = await getToken();
    if (token == null || token.isEmpty) return null;

    final cacheKey = 'loyalty_$companyId';
    if (!forceRefresh && _cache.containsKey(cacheKey) && _cache[cacheKey]!.isValid(const Duration(seconds: 30))) {
      return _cache[cacheKey]!.data as LoyaltyAccountItem;
    }

    try {
      final response = await _get(
        '/loyalty/?company_id=$companyId',
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        final item = LoyaltyAccountItem.fromJson(data);
        _cache[cacheKey] = _CacheEntry<LoyaltyAccountItem>(item);
        return item;
      }
    } catch (_) {}
    return _cache.containsKey(cacheKey) ? (_cache[cacheKey]!.data as LoyaltyAccountItem) : null;
  }

  static Future<List<LoyaltyAccountItem>> getAllLoyaltyAccounts({bool forceRefresh = false}) async {
    final token = await getToken();
    if (token == null || token.isEmpty) return [];

    const cacheKey = 'all_loyalty';
    if (!forceRefresh && _cache.containsKey(cacheKey) && _cache[cacheKey]!.isValid(const Duration(seconds: 30))) {
      return _cache[cacheKey]!.data as List<LoyaltyAccountItem>;
    }

    try {
      final response = await _get(
        '/loyalty/all/',
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final List data = jsonDecode(utf8.decode(response.bodyBytes));
        final list = data.map((item) => LoyaltyAccountItem.fromJson(item)).toList();
        _cache[cacheKey] = _CacheEntry<List<LoyaltyAccountItem>>(list);
        return list;
      }
    } catch (_) {}
    return _cache.containsKey(cacheKey) ? (_cache[cacheKey]!.data as List<LoyaltyAccountItem>) : [];
  }
}
