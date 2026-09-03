import 'package:flutter/foundation.dart';

class ApiConfig {
  // IP da máquina na rede local para acesso via celular/tablet/navegador
  static const String localIp = '192.168.1.109';
  static const String serverPort = '8000';

  static String get baseUrl {
    if (kIsWeb) {
      return 'http://127.0.0.1:$serverPort/api/v1';
    } else {
      // Celular físico na mesma rede Wi-Fi ou emulador
      return 'http://$localIp:$serverPort/api/v1';
    }
  }
}
