class ApiConfig {
  // IP da máquina na rede local ou localhost via USB adb reverse
  static const String localIp = '127.0.0.1'; // USB adb reverse ou Web
  static const String wifiIp = '192.168.1.109'; // Wi-Fi Local
  static const String serverPort = '8000';

  static String get baseUrl => 'http://$localIp:$serverPort/api/v1';
  static String get fallbackUrl => 'http://$wifiIp:$serverPort/api/v1';
}
