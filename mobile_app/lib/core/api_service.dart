import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'api_config.dart';
import 'models.dart';

class ApiService {
  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  static Future<bool> login(String email, String password) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/auth/login/');
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('access_token', data['access']);
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
  }

  static Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  static Future<List<Company>> getCompanies() async {
    final url = Uri.parse('${ApiConfig.baseUrl}/companies/');
    try {
      final response = await http.get(url).timeout(const Duration(seconds: 8));
      if (response.statusCode == 200) {
        final List data = jsonDecode(utf8.decode(response.bodyBytes));
        return data.map((item) => Company.fromJson(item)).toList();
      }
    } catch (_) {
      // Falha de conexão ou servidor offline tratada silenciosamente
    }
    return [];
  }

  static Future<List<ServiceItem>> getServices(int companyId) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/companies/$companyId/services/');
    try {
      final response = await http.get(url).timeout(const Duration(seconds: 8));
      if (response.statusCode == 200) {
        final List data = jsonDecode(utf8.decode(response.bodyBytes));
        return data.map((item) => ServiceItem.fromJson(item)).toList();
      }
    } catch (_) {
      // Falha tratada silenciosamente
    }
    return [];
  }

  static Future<List<VehicleItem>> getMyVehicles() async {
    final token = await getToken();
    if (token == null || token.isEmpty) return [];

    final url = Uri.parse('${ApiConfig.baseUrl}/vehicles/');
    try {
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      ).timeout(const Duration(seconds: 8));

      if (response.statusCode == 200) {
        final List data = jsonDecode(utf8.decode(response.bodyBytes));
        return data.map((item) => VehicleItem.fromJson(item)).toList();
      }
    } catch (_) {
      // Falha tratada silenciosamente
    }
    return [];
  }

  static Future<bool> createVehicle({
    required int companyId,
    required String plate,
    required String brand,
    required String model,
    required String color,
    String vehicleType = 'sedan',
  }) async {
    final token = await getToken();
    if (token == null || token.isEmpty) return false;

    final url = Uri.parse('${ApiConfig.baseUrl}/vehicles/');
    try {
      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'company': companyId,
          'plate': plate,
          'brand': brand,
          'model': model,
          'color': color,
          'vehicle_type': vehicleType,
        }),
      ).timeout(const Duration(seconds: 8));

      return response.statusCode == 201 || response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<List<ServiceOrderItem>> getMyOrders() async {
    final token = await getToken();
    if (token == null || token.isEmpty) return [];

    final url = Uri.parse('${ApiConfig.baseUrl}/orders/');
    try {
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      ).timeout(const Duration(seconds: 8));

      if (response.statusCode == 200) {
        final List data = jsonDecode(utf8.decode(response.bodyBytes));
        return data.map((item) => ServiceOrderItem.fromJson(item)).toList();
      }
    } catch (_) {
      // Falha tratada silenciosamente
    }
    return [];
  }

  static Future<LoyaltyBalance?> getLoyaltyBalance(int companyId) async {
    final token = await getToken();
    if (token == null || token.isEmpty) return null;

    final url = Uri.parse('${ApiConfig.baseUrl}/loyalty/?company_id=$companyId');
    try {
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      ).timeout(const Duration(seconds: 8));

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        return LoyaltyBalance.fromJson(data);
      }
    } catch (_) {
      // Falha tratada silenciosamente
    }
    return null;
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

    final url = Uri.parse('${ApiConfig.baseUrl}/appointments/book/');
    try {
      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'company': companyId,
          'vehicle': vehicleId,
          'service_type': serviceTypeId,
          'scheduled_date': date,
          'scheduled_time': time,
          'notes': notes,
        }),
      ).timeout(const Duration(seconds: 8));

      return response.statusCode == 201;
    } catch (_) {
      return false;
    }
  }
}
