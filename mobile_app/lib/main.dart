import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:intl/intl.dart';
import 'package:audioplayers/audioplayers.dart';
import 'core/models.dart';
import 'core/api_service.dart';
import 'widgets/brazilian_plate_widget.dart';

void main() {
  runApp(const AutoFlowApp());
}

class AutoFlowApp extends StatelessWidget {
  const AutoFlowApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AutoFlow Mobile - Estética Automotiva VIP',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF121519),
        primaryColor: const Color(0xFFD4AF37),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFFD4AF37),
          secondary: Color(0xFFA3734C),
          surface: Color(0xFF1E232A),
          tertiary: Color(0xFF1EA8D7),
        ),
        textTheme: GoogleFonts.plusJakartaSansTextTheme(
          ThemeData(brightness: Brightness.dark).textTheme,
        ),
        useMaterial3: true,
      ),
      home: const MainScreen(),
    );
  }
}

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _globalTabIndex = 0; // 0: Início, 1: Meu Carro, 2: Fidelidade, 3: Garagem, 4: Agendamentos
  int _storeTabIndex = 0;  // 0: Catálogo, 1: Fidelidade, 2: Garagem, 3: Sobre

  bool _isSelectingCompany = true; // true = Rede AutoFlow Global; false = Loja do Lava-Jato
  Company? _selectedCompany;

  List<Company> _companies = [];
  List<ServiceItem> _services = [];
  List<ServiceOrderItem> _orders = [];
  List<VehicleItem> _myVehicles = [];
  List<AppointmentItem> _appointments = [];
  List<LoyaltyAccountItem> _loyaltyAccounts = [];
  LoyaltyAccountItem? _selectedCompanyLoyalty;

  bool _isLoading = true;
  bool _isLoggedIn = false;
  String? _userDisplayName;
  String _searchQuery = '';
  final TextEditingController _searchController = TextEditingController();

  final AudioPlayer _audioPlayer = AudioPlayer();
  Timer? _livePollingTimer;
  final Map<int, String> _knownOrderStatuses = {};

  @override
  void initState() {
    super.initState();
    _loadInitialData();
    _startLiveOrderMonitoring();
  }

  @override
  void dispose() {
    _livePollingTimer?.cancel();
    _audioPlayer.dispose();
    _searchController.dispose();
    super.dispose();
  }

  void _startLiveOrderMonitoring() {
    _livePollingTimer?.cancel();
    _livePollingTimer = Timer.periodic(const Duration(seconds: 4), (timer) async {
      if (!_isLoggedIn) return;

      try {
        final latestOrders = await ApiService.getMyOrders(forceRefresh: true);
        if (!mounted) return;

        bool hasStatusChange = false;

        for (final order in latestOrders) {
          final orderId = order.id;
          final currentStatus = order.status;
          final previousStatus = _knownOrderStatuses[orderId];

          if (previousStatus != null && previousStatus != currentStatus) {
            hasStatusChange = true;
            _handleStatusTransition(order, previousStatus, currentStatus);
          }

          _knownOrderStatuses[orderId] = currentStatus;
        }

        if (hasStatusChange && mounted) {
          setState(() {
            _orders = latestOrders;
          });
        }
      } catch (_) {}
    });
  }

  void _handleStatusTransition(ServiceOrderItem order, String fromStatus, String toStatus) {
    if (toStatus == 'in_progress' || toStatus == 'washing') {
      _playSportHorn();
      _showVIPBannerNotification(
        title: '🏎️💨 Carro em Atendimento!',
        message: 'O seu veículo ${order.vehiclePlate} (${order.vehicleBrand} ${order.vehicleModel}) entrou EM ATENDIMENTO na unidade ${order.companyName}! (Fom-Fom!)',
        isCompleted: false,
      );
    } else if (toStatus == 'completed') {
      _playSpeedEnginePass();
      _showVIPBannerNotification(
        title: '🏁✨ Pronto para Retirada!',
        message: 'VRUMMM! O seu veículo ${order.vehiclePlate} (${order.vehicleBrand} ${order.vehicleModel}) está PRONTO PARA RETIRADA na unidade ${order.companyName}!',
        isCompleted: true,
      );
    }
  }

  void _playSportHorn() {
    HapticFeedback.heavyImpact();
    try {
      _audioPlayer.stop();
      _audioPlayer.play(AssetSource('audio/horn.wav'));
    } catch (_) {}
  }

  void _playSpeedEnginePass() {
    HapticFeedback.heavyImpact();
    try {
      _audioPlayer.stop();
      _audioPlayer.play(AssetSource('audio/vrumm.wav'));
    } catch (_) {}
  }

  void _showVIPBannerNotification({
    required String title,
    required String message,
    required bool isCompleted,
  }) {
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
        duration: const Duration(seconds: 8),
        content: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF1E232A),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: isCompleted ? const Color(0xFF10B981) : const Color(0xFF1EA8D7),
              width: 1.5,
            ),
            boxShadow: [
              BoxShadow(
                color: (isCompleted ? const Color(0xFF10B981) : const Color(0xFF1EA8D7)).withValues(alpha: 0.25),
                blurRadius: 16,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: (isCompleted ? const Color(0xFF10B981) : const Color(0xFF1EA8D7)).withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  isCompleted ? Icons.auto_awesome : Icons.local_car_wash,
                  color: isCompleted ? const Color(0xFF34D399) : const Color(0xFF38C5EE),
                  size: 22,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: Colors.white),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      message,
                      style: const TextStyle(fontSize: 12, color: Color(0xFFD1D5DB)),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Company? get _lastVisitedCompany {
    if (_orders.isNotEmpty) {
      final firstOrder = _orders.first;
      for (final c in _companies) {
        if (c.name.toLowerCase() == firstOrder.companyName.toLowerCase() || c.id == firstOrder.id) {
          return c;
        }
      }
    }
    if (_appointments.isNotEmpty) {
      final firstAppt = _appointments.first;
      for (final c in _companies) {
        if (c.id == firstAppt.companyId || c.name.toLowerCase() == firstAppt.companyName.toLowerCase()) {
          return c;
        }
      }
    }
    return _companies.isNotEmpty ? _companies.first : null;
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoading = true);
    final loggedIn = await ApiService.isLoggedIn();
    final displayName = await ApiService.getUserDisplayName();
    final companies = await ApiService.getCompanies();

    List<ServiceOrderItem> orders = [];
    List<VehicleItem> vehicles = [];
    List<AppointmentItem> appointments = [];
    List<LoyaltyAccountItem> loyaltyAccounts = [];

    if (loggedIn) {
      orders = await ApiService.getMyOrders(forceRefresh: true);
      vehicles = await ApiService.getMyVehicles(forceRefresh: true);
      appointments = await ApiService.getAppointments(forceRefresh: true);
      loyaltyAccounts = await ApiService.getAllLoyaltyAccounts(forceRefresh: true);

      // Sincroniza estado base para detecção de transições futuras
      for (final o in orders) {
        _knownOrderStatuses[o.id] = o.status;
      }
    }

    setState(() {
      _companies = companies;
      _orders = orders;
      _myVehicles = vehicles;
      _appointments = appointments;
      _loyaltyAccounts = loyaltyAccounts;
      _isLoggedIn = loggedIn;
      _userDisplayName = displayName;
      _isLoading = false;
    });

    if (_selectedCompany != null) {
      _loadCompanyDetails(_selectedCompany!);
    }
  }

  Future<void> _loadCompanyDetails(Company company) async {
    final services = await ApiService.getServices(company.id);
    LoyaltyAccountItem? loyalty;
    if (_isLoggedIn && company.features.hasLoyalty) {
      loyalty = await ApiService.getLoyaltyBalance(company.id);
    }
    setState(() {
      _services = services;
      _selectedCompanyLoyalty = loyalty;
    });
  }

  void _selectCompany(Company company) {
    setState(() {
      _selectedCompany = company;
      _isSelectingCompany = false;
      _storeTabIndex = 0;
    });
    _loadCompanyDetails(company);
  }

  void _backToGlobalNetwork([int tabIndex = 0]) {
    setState(() {
      _isSelectingCompany = true;
      _globalTabIndex = tabIndex;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        backgroundColor: Color(0xFF121519),
        body: Center(
          child: CircularProgressIndicator(color: Color(0xFF1EA8D7)),
        ),
      );
    }

    final isTablet = MediaQuery.sizeOf(context).width >= 600;

    if (_isSelectingCompany || _selectedCompany == null) {
      return _buildGlobalNetworkScreen(isTablet);
    } else {
      return _buildStoreScreen(isTablet);
    }
  }

  // ===========================================================================
  // 1. TELA GLOBAL DA REDE AUTOFLOW (INÍCIO)
  // ===========================================================================
  Widget _buildGlobalNetworkScreen(bool isTablet) {
    final List<Widget> pages = [
      _buildHomeDiscoveryTab(isTablet),
      _buildMyCarLiveTrackingTab(isTablet),
      _buildLoyaltyGlobalTab(isTablet),
      _buildGarageGlobalTab(isTablet),
      _buildAppointmentsGlobalTab(isTablet),
    ];

    final List<NavigationDestination> destinations = const [
      NavigationDestination(
        icon: Icon(Icons.home_outlined, color: Color(0xFF9A9FA8)),
        selectedIcon: Icon(Icons.home, color: Color(0xFF1EA8D7)),
        label: 'Início',
      ),
      NavigationDestination(
        icon: Icon(Icons.directions_car_outlined, color: Color(0xFF9A9FA8)),
        selectedIcon: Icon(Icons.directions_car, color: Color(0xFF1EA8D7)),
        label: 'Meu Carro',
      ),
      NavigationDestination(
        icon: Icon(Icons.card_giftcard_outlined, color: Color(0xFF9A9FA8)),
        selectedIcon: Icon(Icons.card_giftcard, color: Color(0xFF1EA8D7)),
        label: 'Fidelidade',
      ),
      NavigationDestination(
        icon: Icon(Icons.key_outlined, color: Color(0xFF9A9FA8)),
        selectedIcon: Icon(Icons.key, color: Color(0xFF1EA8D7)),
        label: 'Garagem',
      ),
      NavigationDestination(
        icon: Icon(Icons.calendar_month_outlined, color: Color(0xFF9A9FA8)),
        selectedIcon: Icon(Icons.calendar_month, color: Color(0xFF1EA8D7)),
        label: 'Agenda',
      ),
    ];

    if (_globalTabIndex >= pages.length) {
      _globalTabIndex = 0;
    }

    return Scaffold(
      backgroundColor: const Color(0xFF121519),
      appBar: _buildGlobalAppBar(),
      body: Row(
        children: [
          if (isTablet)
            NavigationRail(
              backgroundColor: const Color(0xFF14171A),
              selectedIndex: _globalTabIndex,
              onDestinationSelected: (idx) => setState(() => _globalTabIndex = idx),
              labelType: NavigationRailLabelType.all,
              destinations: const [
                NavigationRailDestination(
                  icon: Icon(Icons.home_outlined),
                  selectedIcon: Icon(Icons.home, color: Color(0xFF1EA8D7)),
                  label: Text('Início'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.directions_car_outlined),
                  selectedIcon: Icon(Icons.directions_car, color: Color(0xFF1EA8D7)),
                  label: Text('Meu Carro'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.card_giftcard_outlined),
                  selectedIcon: Icon(Icons.card_giftcard, color: Color(0xFF1EA8D7)),
                  label: Text('Fidelidade'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.key_outlined),
                  selectedIcon: Icon(Icons.key, color: Color(0xFF1EA8D7)),
                  label: Text('Garagem'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.calendar_month_outlined),
                  selectedIcon: Icon(Icons.calendar_month, color: Color(0xFF1EA8D7)),
                  label: Text('Agenda'),
                ),
              ],
            ),
          Expanded(child: pages[_globalTabIndex]),
        ],
      ),
      bottomNavigationBar: !isTablet
          ? Container(
              decoration: const BoxDecoration(
                color: Color(0xFF14171A),
                border: Border(top: BorderSide(color: Color(0x33A3734C), width: 1)),
              ),
              child: NavigationBar(
                backgroundColor: const Color(0xFF14171A),
                indicatorColor: const Color(0xFF1EA8D7).withValues(alpha: 0.2),
                selectedIndex: _globalTabIndex,
                onDestinationSelected: (idx) => setState(() => _globalTabIndex = idx),
                destinations: destinations,
              ),
            )
          : null,
    );
  }

  PreferredSizeWidget _buildGlobalAppBar() {
    return AppBar(
      backgroundColor: const Color(0xFF14171A),
      elevation: 0,
      titleSpacing: 16,
      title: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: const Color(0xFF121519),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.5)),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFFD4AF37).withValues(alpha: 0.2),
                  blurRadius: 8,
                ),
              ],
            ),
            padding: const EdgeInsets.all(3),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.asset(
                'assets/images/logo.png',
                fit: BoxFit.contain,
                errorBuilder: (context, error, stackTrace) => const Icon(
                  Icons.auto_awesome,
                  color: Color(0xFFD4AF37),
                  size: 20,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'AutoFlow',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: Colors.white),
              ),
              Text(
                'ESTÉTICA AUTOMOTIVA',
                style: TextStyle(
                  fontSize: 9,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.1,
                  color: const Color(0xFFD4AF37).withValues(alpha: 0.9),
                ),
              ),
            ],
          ),
        ],
      ),
      actions: [
        if (_isLoggedIn) ...[
          Container(
            margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0xFF1E232A),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.3)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: Color(0xFF1EA8D7),
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 6),
                Text(
                  _userDisplayName ?? 'VIP',
                  style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.white),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.logout, size: 20, color: Color(0xFF9A9FA8)),
            tooltip: 'Sair da Conta',
            onPressed: () async {
              await ApiService.logout();
              await _loadInitialData();
            },
          ),
        ] else ...[
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: ElevatedButton.icon(
              onPressed: _showLoginModal,
              icon: const Icon(Icons.login, size: 16),
              label: const Text('Entrar VIP'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFD4AF37),
                foregroundColor: const Color(0xFF121519),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ),
        ],
      ],
    );
  }

  // ===========================================================================
  // ABA 1: INÍCIO (BUSCA & DESCOBERTA DE LAVA-JATOS CREDENCIADOS)
  // ===========================================================================
  Widget _buildHomeDiscoveryTab(bool isTablet) {
    final filteredCompanies = _companies.where((c) {
      if (_searchQuery.isEmpty) return true;
      final query = _searchQuery.toLowerCase();
      return c.name.toLowerCase().contains(query) ||
          c.address.toLowerCase().contains(query) ||
          c.city.toLowerCase().contains(query);
    }).toList();

    return RefreshIndicator(
      color: const Color(0xFF1EA8D7),
      backgroundColor: const Color(0xFF1E232A),
      onRefresh: _loadInitialData,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Banner Topo com Logo e Título
          Container(
            padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  const Color(0xFF1E232A),
                  const Color(0xFF14171A).withValues(alpha: 0.9),
                ],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.3)),
            ),
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFFD4AF37).withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.3)),
                  ),
                  child: const Text(
                    '★ ★ ★ ★ ★  REDE DE ESTÉTICA AUTOMOTIVA',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w900,
                      color: Color(0xFFF5E6BE),
                      letterSpacing: 1.0,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                const Text(
                  'Onde vamos cuidar do seu veículo hoje?',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: Colors.white, height: 1.2),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Selecione o lava-jato credenciado para agendar serviços de polimento, vitrificação e lavagem com padrão 5 estrelas.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 12, color: Color(0xFF9A9FA8)),
                ),
                const SizedBox(height: 18),

                // Barra de Busca
                TextField(
                  controller: _searchController,
                  onChanged: (val) => setState(() => _searchQuery = val.trim()),
                  style: const TextStyle(fontSize: 13, color: Colors.white),
                  decoration: InputDecoration(
                    filled: true,
                    fillColor: const Color(0xFF121519),
                    hintText: 'Buscar por nome, bairro ou endereço...',
                    hintStyle: const TextStyle(color: Color(0xFF6B7280), fontSize: 13),
                    prefixIcon: const Icon(Icons.search, color: Color(0xFFD4AF37), size: 20),
                    suffixIcon: _searchQuery.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, color: Color(0xFF9A9FA8), size: 18),
                            onPressed: () {
                              _searchController.clear();
                              setState(() => _searchQuery = '');
                            },
                          )
                        : null,
                    contentPadding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: BorderSide(color: const Color(0xFFD4AF37).withValues(alpha: 0.4)),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: const BorderSide(color: Color(0xFF1EA8D7), width: 1.5),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: BorderSide(color: const Color(0xFFA3734C).withValues(alpha: 0.3)),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Card do Último Lava-Jato Visitado
          if (_lastVisitedCompany != null && _searchQuery.isEmpty) ...[
            _buildLastVisitedCard(_lastVisitedCompany!),
            const SizedBox(height: 24),
          ],

          // Título Centros Credenciados
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Row(
                children: [
                  Icon(Icons.storefront, color: Color(0xFFD4AF37), size: 20),
                  SizedBox(width: 8),
                  Text(
                    'Centros Credenciados',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                ],
              ),
              Text(
                '${filteredCompanies.length} unidades',
                style: const TextStyle(fontSize: 12, color: Color(0xFF9A9FA8)),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Lista / Grid de Lava-jatos
          if (filteredCompanies.isEmpty)
            Container(
              padding: const EdgeInsets.all(32),
              decoration: BoxDecoration(
                color: const Color(0xFF1E232A).withValues(alpha: 0.5),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: Colors.white10),
              ),
              child: const Column(
                children: [
                  Icon(Icons.search_off, size: 40, color: Color(0xFF6B7280)),
                  SizedBox(height: 12),
                  Text('Nenhum lava-jato encontrado', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                  SizedBox(height: 4),
                  Text('Tente buscar por outro termo ou bairro.', style: TextStyle(color: Color(0xFF9A9FA8), fontSize: 12)),
                ],
              ),
            )
          else
            ...filteredCompanies.map((c) => _buildCompanyCard(c)),
        ],
      ),
    );
  }

  Widget _buildLastVisitedCard(Company company) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFFD4AF37).withValues(alpha: 0.15),
            const Color(0xFF1E232A),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.4)),
      ),
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0xFFD4AF37).withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.history, size: 14, color: Color(0xFFF5E6BE)),
                SizedBox(width: 4),
                Text(
                  'ÚLTIMO LAVA-JATO QUE VOCÊ FOI',
                  style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: Color(0xFFF5E6BE)),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: const Color(0xFF121519),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.5)),
                ),
                padding: const EdgeInsets.all(4),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: (company.logo != null && company.logo!.isNotEmpty)
                      ? CachedNetworkImage(
                          imageUrl: company.logo!,
                          fit: BoxFit.contain,
                          errorWidget: (c, u, e) => const Icon(Icons.store, color: Color(0xFFD4AF37)),
                        )
                      : const Icon(Icons.store, color: Color(0xFFD4AF37)),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      company.name,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                    Text(
                      company.address.isNotEmpty ? company.address : company.city,
                      style: const TextStyle(fontSize: 12, color: Color(0xFF9A9FA8)),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => _selectCompany(company),
                  icon: const Icon(Icons.arrow_forward, size: 16),
                  label: const Text('Desejo ir neste novamente'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFD4AF37),
                    foregroundColor: const Color(0xFF121519),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w900),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCompanyCard(Company company) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      decoration: BoxDecoration(
        color: const Color(0xFF1E232A),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.3)),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  color: const Color(0xFF121519),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.4)),
                ),
                padding: const EdgeInsets.all(3),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(9),
                  child: (company.logo != null && company.logo!.isNotEmpty)
                      ? CachedNetworkImage(
                          imageUrl: company.logo!,
                          fit: BoxFit.contain,
                          errorWidget: (context, url, error) => const Icon(Icons.store, color: Color(0xFFD4AF37)),
                        )
                      : const Icon(Icons.store, color: Color(0xFFD4AF37)),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            company.name,
                            style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: const Color(0xFFD4AF37).withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.3)),
                          ),
                          child: const Text(
                            'CREDENCIADO',
                            style: TextStyle(fontSize: 9, fontWeight: FontWeight.w900, color: Color(0xFFF5E6BE)),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        const Icon(Icons.location_on, size: 12, color: Color(0xFF1EA8D7)),
                        const SizedBox(width: 3),
                        Expanded(
                          child: Text(
                            company.address.isNotEmpty ? company.address : company.city,
                            style: const TextStyle(fontSize: 11, color: Color(0xFF9A9FA8)),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Badges de Features
          Wrap(
            spacing: 6,
            runSpacing: 4,
            children: [
              _buildFeatureChip(Icons.calendar_today, 'Agendamento Online'),
              if (company.features.hasInspections)
                _buildFeatureChip(Icons.camera_alt, 'Vistoria Fotográfica'),
              if (company.features.hasLoyalty)
                _buildFeatureChip(Icons.stars, 'Clube Fidelidade'),
            ],
          ),
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () => _selectCompany(company),
              icon: const Icon(Icons.login, size: 16),
              label: const Text('Acessar este Lava-Jato'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF1EA8D7).withValues(alpha: 0.15),
                foregroundColor: const Color(0xFF38C5EE),
                side: const BorderSide(color: Color(0x661EA8D7)),
                padding: const EdgeInsets.symmetric(vertical: 11),
                textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeatureChip(IconData icon, String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: const Color(0xFF121519),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.white12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 11, color: const Color(0xFFD4AF37)),
          const SizedBox(width: 4),
          Text(text, style: const TextStyle(fontSize: 10, color: Color(0xFF9A9FA8))),
        ],
      ),
    );
  }

  // ===========================================================================
  // ABA 2: MEU CARRO (ACOMPANHAMENTO EM TEMPO REAL MULTI-UNIDADE)
  // ===========================================================================
  Widget _buildMyCarLiveTrackingTab(bool isTablet) {
    final activeOrders = _orders.where((o) => o.status != 'delivered' && o.status != 'cancelled').toList();
    final recentOrders = _orders.where((o) => o.status == 'delivered' || o.status == 'completed').toList();

    return RefreshIndicator(
      color: const Color(0xFF1EA8D7),
      backgroundColor: const Color(0xFF1E232A),
      onRefresh: _loadInitialData,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Row(
            children: [
              Icon(Icons.directions_car, color: Color(0xFF10B981), size: 22),
              SizedBox(width: 8),
              Text(
                'Acompanhamento em Tempo Real',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: Colors.white),
              ),
            ],
          ),
          const SizedBox(height: 4),
          const Text(
            'Acompanhe o status e a vistoria de todos os seus carros em atendimento na rede credenciada.',
            style: TextStyle(fontSize: 12, color: Color(0xFF9A9FA8)),
          ),
          const SizedBox(height: 16),

          if (activeOrders.isEmpty)
            Container(
              padding: const EdgeInsets.all(28),
              decoration: BoxDecoration(
                color: const Color(0xFF1E232A),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.white10),
              ),
              child: Column(
                children: [
                  const Icon(Icons.no_crash, size: 48, color: Color(0xFF6B7280)),
                  const SizedBox(height: 12),
                  const Text(
                    'Nenhum veículo em atendimento no momento',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Assim que der entrada em um lava-jato parceiro, você poderá acompanhar todo o processo e fotos por aqui.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12, color: Color(0xFF9A9FA8)),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: () => _backToGlobalNetwork(0),
                    icon: const Icon(Icons.storefront, size: 16),
                    label: const Text('Ver Lava-Jatos Disponíveis'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFD4AF37),
                      foregroundColor: const Color(0xFF121519),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ],
              ),
            )
          else
            ...activeOrders.map((o) => _buildActiveOrderCard(o)),

          if (recentOrders.isNotEmpty) ...[
            const SizedBox(height: 24),
            const Text(
              'Últimos Atendimentos Concluídos',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            const SizedBox(height: 10),
            ...recentOrders.take(5).map((o) => _buildRecentOrderTile(o)),
          ],
        ],
      ),
    );
  }

  Widget _buildActiveOrderCard(ServiceOrderItem order) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E232A),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.35)),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header com Placa e Unidade
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              BrazilianPlateWidget(rawPlate: order.vehiclePlate, size: PlateSize.sm),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${order.vehicleBrand} ${order.vehicleModel}'.trim().isNotEmpty
                          ? '${order.vehicleBrand} ${order.vehicleModel}'
                          : order.serviceName,
                      style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                    const SizedBox(height: 4),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: const Color(0xFFD4AF37).withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.3)),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.store, size: 12, color: Color(0xFFD4AF37)),
                          const SizedBox(width: 4),
                          Flexible(
                            child: Text(
                              order.companyName,
                              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFFF5E6BE)),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: const Color(0xFF1EA8D7).withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF1EA8D7).withValues(alpha: 0.5)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 6,
                      height: 6,
                      decoration: const BoxDecoration(
                        color: Color(0xFF1EA8D7),
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 5),
                    Text(
                      order.statusLabel,
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: Color(0xFF38C5EE)),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Informações de Serviço
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFF121519),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Serviço Contratado', style: TextStyle(fontSize: 10, color: Color(0xFF9A9FA8))),
                    Text(order.serviceName, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white)),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    const Text('Valor Total', style: TextStyle(fontSize: 10, color: Color(0xFF9A9FA8))),
                    Text('R\$ ${order.finalPrice.toStringAsFixed(2)}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w900, color: Color(0xFF10B981))),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Timeline 4 Etapas
          _buildStageTimeline(order.currentStep),

          // Fotos de Vistoria
          if (order.photos.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text(
              'Vistoria Fotográfica no Pátio:',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFFD4AF37)),
            ),
            const SizedBox(height: 8),
            SizedBox(
              height: 90,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: order.photos.length,
                itemBuilder: (context, idx) {
                  final photo = order.photos[idx];
                  return GestureDetector(
                    onTap: () => _showPhotoZoom(photo.imageUrl, photo.caption),
                    child: Container(
                      width: 90,
                      margin: const EdgeInsets.only(right: 10),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: const Color(0xFF1EA8D7).withValues(alpha: 0.5)),
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(13),
                        child: CachedNetworkImage(
                          imageUrl: photo.imageUrl,
                          fit: BoxFit.cover,
                          placeholder: (context, url) => const Center(child: CircularProgressIndicator(strokeWidth: 2)),
                          errorWidget: (context, url, error) => const Icon(Icons.broken_image, color: Colors.grey),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStageTimeline(int currentStep) {
    final stages = [
      {'num': 1, 'label': 'Na Fila', 'icon': Icons.queue},
      {'num': 2, 'label': 'Em Atendimento', 'icon': Icons.cleaning_services},
      {'num': 3, 'label': 'Pronto', 'icon': Icons.check_circle},
      {'num': 4, 'label': 'Entregue', 'icon': Icons.key},
    ];

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: stages.map((s) {
        final stepNum = s['num'] as int;
        final isActive = stepNum <= currentStep;
        final isCurrent = stepNum == currentStep;

        return Expanded(
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 2),
            padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
            decoration: BoxDecoration(
              color: isCurrent
                  ? const Color(0xFF1EA8D7).withValues(alpha: 0.25)
                  : (isActive ? const Color(0xFF10B981).withValues(alpha: 0.15) : const Color(0xFF121519)),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: isCurrent
                    ? const Color(0xFF1EA8D7)
                    : (isActive ? const Color(0xFF10B981) : Colors.white10),
                width: isCurrent ? 1.5 : 1,
              ),
            ),
            child: Column(
              children: [
                Icon(
                  s['icon'] as IconData,
                  size: 16,
                  color: isCurrent
                      ? const Color(0xFF38C5EE)
                      : (isActive ? const Color(0xFF10B981) : const Color(0xFF6B7280)),
                ),
                const SizedBox(height: 4),
                Text(
                  s['label'] as String,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 9,
                    fontWeight: isCurrent ? FontWeight.w900 : FontWeight.bold,
                    color: isCurrent ? Colors.white : (isActive ? const Color(0xFF10B981) : const Color(0xFF6B7280)),
                  ),
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildRecentOrderTile(ServiceOrderItem order) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF1E232A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: Row(
        children: [
          BrazilianPlateWidget(rawPlate: order.vehiclePlate, size: PlateSize.sm),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(order.serviceName, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.white)),
                Text(order.companyName, style: const TextStyle(fontSize: 11, color: Color(0xFFD4AF37))),
              ],
            ),
          ),
          Text(
            'R\$ ${order.finalPrice.toStringAsFixed(2)}',
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF10B981)),
          ),
        ],
      ),
    );
  }

  // ===========================================================================
  // ABA 3: FIDELIDADE GLOBAL (TODAS AS UNIDADES)
  // ===========================================================================
  Widget _buildLoyaltyGlobalTab(bool isTablet) {
    return RefreshIndicator(
      color: const Color(0xFF1EA8D7),
      backgroundColor: const Color(0xFF1E232A),
      onRefresh: _loadInitialData,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Row(
            children: [
              Icon(Icons.stars, color: Color(0xFFEC4899), size: 22),
              SizedBox(width: 8),
              Text(
                'Programa de Fidelidade VIP',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: Colors.white),
              ),
            ],
          ),
          const SizedBox(height: 4),
          const Text(
            'Consulte seus pontos acumulados e prêmios em cada centro de estética credenciado.',
            style: TextStyle(fontSize: 12, color: Color(0xFF9A9FA8)),
          ),
          const SizedBox(height: 16),

          if (_loyaltyAccounts.isEmpty)
            Container(
              padding: const EdgeInsets.all(28),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF831843), Color(0xFF1E232A)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: const Color(0xFFEC4899).withValues(alpha: 0.3)),
              ),
              child: Column(
                children: [
                  const Icon(Icons.card_giftcard, size: 48, color: Color(0xFFF472B6)),
                  const SizedBox(height: 12),
                  Text(
                    _isLoggedIn ? 'Cartão Fidelidade AutoFlow VIP' : 'Faça Login para Acessar seus Pontos',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Ao realizar serviços em lava-jatos credenciados, você acumula pontos automaticamente para resgatar lavagens grátis.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12, color: Color(0xFFFBCFE8)),
                  ),
                  if (!_isLoggedIn) ...[
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: _showLoginModal,
                      style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFEC4899)),
                      child: const Text('Fazer Login VIP', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ],
              ),
            )
          else
            ..._loyaltyAccounts.map((acc) => _buildLoyaltyCard(acc)),
        ],
      ),
    );
  }

  Widget _buildLoyaltyCard(LoyaltyAccountItem account) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF831843), Color(0xFF1E232A)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFFEC4899).withValues(alpha: 0.4)),
      ),
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    account.companyName,
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: Colors.white),
                  ),
                  Text(
                    account.companyCity.isNotEmpty ? account.companyCity : 'Unidade Parceira',
                    style: const TextStyle(fontSize: 11, color: Color(0xFFFBCFE8)),
                  ),
                ],
              ),
              const Icon(Icons.workspace_premium, color: Color(0xFFF472B6), size: 28),
            ],
          ),
          const SizedBox(height: 20),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                '${account.pointsBalance}',
                style: const TextStyle(fontSize: 36, fontWeight: FontWeight.w900, color: Colors.white),
              ),
              const SizedBox(width: 6),
              const Text('pontos VIP', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFFF472B6))),
              const Spacer(),
              Text('Meta: ${account.pointsNeeded} pts', style: const TextStyle(fontSize: 12, color: Color(0xFFFBCFE8))),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: account.progressPercentage,
              backgroundColor: Colors.black26,
              valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFFF472B6)),
              minHeight: 8,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.black38,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              children: [
                const Icon(Icons.emoji_events, size: 14, color: Color(0xFFD4AF37)),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    'Recompensa: ${account.rewardDescription}',
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ===========================================================================
  // ABA 4: GARAGEM GLOBAL (MEUS CARROS)
  // ===========================================================================
  Widget _buildGarageGlobalTab(bool isTablet) {
    return RefreshIndicator(
      color: const Color(0xFF1EA8D7),
      backgroundColor: const Color(0xFF1E232A),
      onRefresh: _loadInitialData,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Row(
                children: [
                  Icon(Icons.key, color: Color(0xFFD4AF37), size: 22),
                  SizedBox(width: 8),
                  Text(
                    'Minha Garagem Digital',
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: Colors.white),
                  ),
                ],
              ),
              if (_isLoggedIn)
                ElevatedButton.icon(
                  onPressed: _showAddVehicleModal,
                  icon: const Icon(Icons.add, size: 16),
                  label: const Text('Cadastrar Carro'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFD4AF37),
                    foregroundColor: const Color(0xFF121519),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    textStyle: const TextStyle(fontSize: 11, fontWeight: FontWeight.w900),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 4),
          const Text(
            'Cadastre e gerencie seus carros para agendamento rápido em qualquer lava-jato da rede.',
            style: TextStyle(fontSize: 12, color: Color(0xFF9A9FA8)),
          ),
          const SizedBox(height: 16),

          if (_myVehicles.isEmpty)
            Container(
              padding: const EdgeInsets.all(28),
              decoration: BoxDecoration(
                color: const Color(0xFF1E232A),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.white10),
              ),
              child: Column(
                children: [
                  const Icon(Icons.directions_car_filled, size: 48, color: Color(0xFF6B7280)),
                  const SizedBox(height: 12),
                  const Text(
                    'Nenhum veículo cadastrado na sua garagem',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Adicione seu carro para agilizar o agendamento em toda a rede AutoFlow.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12, color: Color(0xFF9A9FA8)),
                  ),
                  const SizedBox(height: 16),
                  if (_isLoggedIn)
                    ElevatedButton.icon(
                      onPressed: _showAddVehicleModal,
                      icon: const Icon(Icons.add, size: 16),
                      label: const Text('Cadastrar Primeiro Carro'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFD4AF37),
                        foregroundColor: const Color(0xFF121519),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    )
                  else
                    ElevatedButton.icon(
                      onPressed: _showLoginModal,
                      icon: const Icon(Icons.login, size: 16),
                      label: const Text('Fazer Login para Salvar'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFD4AF37),
                        foregroundColor: const Color(0xFF121519),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                ],
              ),
            )
          else
            ..._myVehicles.map((v) => _buildVehicleCard(v)),
        ],
      ),
    );
  }

  Widget _buildVehicleCard(VehicleItem vehicle) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E232A),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          BrazilianPlateWidget(rawPlate: vehicle.plate, size: PlateSize.md),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${vehicle.brand} ${vehicle.model}',
                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                const SizedBox(height: 2),
                Text(
                  'Cor: ${vehicle.color.isNotEmpty ? vehicle.color : "Não informada"} • ${vehicle.vehicleType.toUpperCase()}',
                  style: const TextStyle(fontSize: 11, color: Color(0xFF9A9FA8)),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline, color: Color(0xFFEF4444), size: 20),
            tooltip: 'Remover Carro',
            onPressed: () => _confirmDeleteVehicle(vehicle),
          ),
        ],
      ),
    );
  }

  // ===========================================================================
  // ABA 5: AGENDAMENTOS GLOBAIS
  // ===========================================================================
  Widget _buildAppointmentsGlobalTab(bool isTablet) {
    return RefreshIndicator(
      color: const Color(0xFF1EA8D7),
      backgroundColor: const Color(0xFF1E232A),
      onRefresh: _loadInitialData,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Row(
            children: [
              Icon(Icons.calendar_month, color: Color(0xFF3B82F6), size: 22),
              SizedBox(width: 8),
              Text(
                'Meus Agendamentos',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: Colors.white),
              ),
            ],
          ),
          const SizedBox(height: 4),
          const Text(
            'Consulte e gerencie seus agendamentos em qualquer lava-jato da rede credenciada.',
            style: TextStyle(fontSize: 12, color: Color(0xFF9A9FA8)),
          ),
          const SizedBox(height: 16),

          if (_appointments.isEmpty)
            Container(
              padding: const EdgeInsets.all(28),
              decoration: BoxDecoration(
                color: const Color(0xFF1E232A),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.white10),
              ),
              child: Column(
                children: [
                  const Icon(Icons.event_busy, size: 48, color: Color(0xFF6B7280)),
                  const SizedBox(height: 12),
                  const Text(
                    'Você não possui agendamentos no momento',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Escolha um dos centros credenciados e reserve um horário para o seu veículo.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12, color: Color(0xFF9A9FA8)),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: () => _backToGlobalNetwork(0),
                    icon: const Icon(Icons.add_circle_outline, size: 16),
                    label: const Text('Agendar Horário'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFD4AF37),
                      foregroundColor: const Color(0xFF121519),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ],
              ),
            )
          else
            ..._appointments.map((appt) => _buildAppointmentCard(appt)),
        ],
      ),
    );
  }

  Widget _buildAppointmentCard(AppointmentItem appt) {
    Color statusColor;
    switch (appt.status) {
      case 'confirmed':
        statusColor = const Color(0xFF10B981);
        break;
      case 'arrived':
        statusColor = const Color(0xFF3B82F6);
        break;
      case 'cancelled':
        statusColor = const Color(0xFFEF4444);
        break;
      default:
        statusColor = const Color(0xFFD4AF37);
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E232A),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                appt.serviceName,
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: statusColor.withValues(alpha: 0.4)),
                ),
                child: Text(
                  appt.statusLabel.toUpperCase(),
                  style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: statusColor),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              const Icon(Icons.store, size: 14, color: Color(0xFFD4AF37)),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  appt.companyName,
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFFF5E6BE)),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              const Icon(Icons.calendar_today, size: 12, color: Color(0xFF1EA8D7)),
              const SizedBox(width: 4),
              Text(
                '${appt.scheduledDate} às ${appt.scheduledTime}',
                style: const TextStyle(fontSize: 12, color: Colors.white),
              ),
              const SizedBox(width: 12),
              const Icon(Icons.directions_car, size: 12, color: Color(0xFF1EA8D7)),
              const SizedBox(width: 4),
              Text(
                appt.vehiclePlate,
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white),
              ),
            ],
          ),
          if (appt.canCancel) ...[
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: () => _confirmCancelAppointment(appt),
                icon: const Icon(Icons.cancel_outlined, size: 14, color: Color(0xFFEF4444)),
                label: const Text('Cancelar Agendamento', style: TextStyle(color: Color(0xFFEF4444), fontSize: 11)),
              ),
            ),
          ],
        ],
      ),
    );
  }

  // ===========================================================================
  // 2. AMBIENTE DO LAVA-JATO ESCOLHIDO (LOJA / STORE VIEW)
  // ===========================================================================
  Widget _buildStoreScreen(bool isTablet) {
    final company = _selectedCompany!;
    final List<Widget> pages = [
      _buildStoreServicesTab(isTablet),
      if (company.features.hasLoyalty) _buildStoreLoyaltyTab(isTablet),
      _buildGarageGlobalTab(isTablet),
      _buildStoreAboutTab(isTablet),
    ];

    final List<NavigationDestination> destinations = [
      const NavigationDestination(
        icon: Icon(Icons.cleaning_services_outlined, color: Color(0xFF9A9FA8)),
        selectedIcon: Icon(Icons.cleaning_services, color: Color(0xFF1EA8D7)),
        label: 'Catálogo',
      ),
      if (company.features.hasLoyalty)
        const NavigationDestination(
          icon: Icon(Icons.card_giftcard_outlined, color: Color(0xFF9A9FA8)),
          selectedIcon: Icon(Icons.card_giftcard, color: Color(0xFF1EA8D7)),
          label: 'Fidelidade',
        ),
      const NavigationDestination(
        icon: Icon(Icons.key_outlined, color: Color(0xFF9A9FA8)),
        selectedIcon: Icon(Icons.key, color: Color(0xFF1EA8D7)),
        label: 'Garagem',
      ),
      const NavigationDestination(
        icon: Icon(Icons.info_outline, color: Color(0xFF9A9FA8)),
        selectedIcon: Icon(Icons.info, color: Color(0xFF1EA8D7)),
        label: 'Sobre',
      ),
    ];

    if (_storeTabIndex >= pages.length) {
      _storeTabIndex = 0;
    }

    return Scaffold(
      backgroundColor: const Color(0xFF121519),
      appBar: AppBar(
        backgroundColor: const Color(0xFF14171A),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Color(0xFFD4AF37)),
          tooltip: 'Voltar para Rede AutoFlow',
          onPressed: () => _backToGlobalNetwork(0),
        ),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              company.name,
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            Text(
              company.address.isNotEmpty ? company.address : company.city,
              style: const TextStyle(fontSize: 10, color: Color(0xFF9A9FA8)),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
        actions: [
          TextButton.icon(
            onPressed: () => _backToGlobalNetwork(0),
            icon: const Icon(Icons.swap_horiz, size: 16, color: Color(0xFFD4AF37)),
            label: const Text('Trocar', style: TextStyle(color: Color(0xFFD4AF37), fontSize: 11, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
      body: pages[_storeTabIndex],
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: Color(0xFF14171A),
          border: Border(top: BorderSide(color: Color(0x33A3734C), width: 1)),
        ),
        child: NavigationBar(
          backgroundColor: const Color(0xFF14171A),
          indicatorColor: const Color(0xFF1EA8D7).withValues(alpha: 0.2),
          selectedIndex: _storeTabIndex,
          onDestinationSelected: (idx) => setState(() => _storeTabIndex = idx),
          destinations: destinations,
        ),
      ),
    );
  }

  Widget _buildStoreServicesTab(bool isTablet) {
    return RefreshIndicator(
      color: const Color(0xFF1EA8D7),
      backgroundColor: const Color(0xFF1E232A),
      onRefresh: () => _loadCompanyDetails(_selectedCompany!),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Row(
                children: [
                  Icon(Icons.cleaning_services, color: Color(0xFFD4AF37), size: 20),
                  SizedBox(width: 8),
                  Text(
                    'Catálogo de Serviços',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                ],
              ),
              Text(
                '${_services.length} opções',
                style: const TextStyle(fontSize: 12, color: Color(0xFF9A9FA8)),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (_services.isEmpty)
            Container(
              padding: const EdgeInsets.all(32),
              decoration: BoxDecoration(
                color: const Color(0xFF1E232A),
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Center(
                child: Text('Nenhum serviço disponível no momento.', style: TextStyle(color: Color(0xFF9A9FA8))),
              ),
            )
          else
            ..._services.map((svc) => _buildServiceCard(svc)),
        ],
      ),
    );
  }

  Widget _buildServiceCard(ServiceItem service) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E232A),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1EA8D7).withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        service.categoryName.toUpperCase(),
                        style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Color(0xFF38C5EE)),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      service.name,
                      style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                  ],
                ),
              ),
              Text(
                'R\$ ${service.price.toStringAsFixed(2)}',
                style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: Color(0xFFD4AF37)),
              ),
            ],
          ),
          if (service.description.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(
              service.description,
              style: const TextStyle(fontSize: 12, color: Color(0xFF9A9FA8)),
            ),
          ],
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(Icons.schedule, size: 14, color: Color(0xFF9A9FA8)),
                  const SizedBox(width: 4),
                  Text('~${service.durationMinutes} min', style: const TextStyle(fontSize: 11, color: Color(0xFF9A9FA8))),
                  if (service.loyaltyPoints > 0) ...[
                    const SizedBox(width: 12),
                    const Icon(Icons.stars, size: 14, color: Color(0xFFEC4899)),
                    const SizedBox(width: 4),
                    Text('+${service.loyaltyPoints} pts', style: const TextStyle(fontSize: 11, color: Color(0xFFF472B6))),
                  ],
                ],
              ),
              ElevatedButton.icon(
                onPressed: () => _showBookingModal(service),
                icon: const Icon(Icons.calendar_today, size: 14),
                label: const Text('Agendar'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFD4AF37),
                  foregroundColor: const Color(0xFF121519),
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  textStyle: const TextStyle(fontSize: 11, fontWeight: FontWeight.w900),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStoreLoyaltyTab(bool isTablet) {
    if (_selectedCompanyLoyalty == null) {
      return const Center(child: Text('Programa de fidelidade não ativo nesta unidade.', style: TextStyle(color: Colors.white70)));
    }
    return _buildLoyaltyCard(_selectedCompanyLoyalty!);
  }

  Widget _buildStoreAboutTab(bool isTablet) {
    final company = _selectedCompany!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0xFF1E232A),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.3)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(company.name, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white)),
              const SizedBox(height: 12),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.location_on, color: Color(0xFFD4AF37)),
                title: const Text('Endereço', style: TextStyle(fontSize: 12, color: Color(0xFF9A9FA8))),
                subtitle: Text(company.address.isNotEmpty ? company.address : company.city, style: const TextStyle(color: Colors.white, fontSize: 13)),
              ),
              if (company.phone.isNotEmpty)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.phone, color: Color(0xFFD4AF37)),
                  title: const Text('Telefone / WhatsApp', style: TextStyle(fontSize: 12, color: Color(0xFF9A9FA8))),
                  subtitle: Text(company.phone, style: const TextStyle(color: Colors.white, fontSize: 13)),
                ),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.verified, color: Color(0xFF10B981)),
                title: const Text('Credenciamento', style: TextStyle(fontSize: 12, color: Color(0xFF9A9FA8))),
                subtitle: const Text('Unidade Oficial Credenciada Rede AutoFlow', style: TextStyle(color: Colors.white, fontSize: 13)),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ===========================================================================
  // MODAIS E FLUXOS INTERATIVOS
  // ===========================================================================
  void _showLoginModal() {
    final emailCtrl = TextEditingController();
    final passCtrl = TextEditingController();
    bool isRegister = false;
    final nameCtrl = TextEditingController();
    final phoneCtrl = TextEditingController();
    bool isLoading = false;
    String? errorMessage;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF1E232A),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(28))),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 24,
                bottom: MediaQuery.of(context).viewInsets.bottom + 24,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        isRegister ? 'Criar Conta VIP AutoFlow' : 'Entrar na Conta VIP',
                        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, color: Color(0xFF9A9FA8)),
                        onPressed: () => Navigator.pop(ctx),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  if (errorMessage != null) ...[
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: Colors.redAccent.withValues(alpha: 0.15),
                        border: Border.all(color: Colors.redAccent.withValues(alpha: 0.5)),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.error_outline, color: Colors.redAccent, size: 18),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              errorMessage!,
                              style: const TextStyle(color: Colors.redAccent, fontSize: 13),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),
                  ],
                  if (isRegister) ...[
                    TextField(
                      controller: nameCtrl,
                      decoration: const InputDecoration(labelText: 'Nome Completo', prefixIcon: Icon(Icons.person)),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: phoneCtrl,
                      keyboardType: TextInputType.phone,
                      decoration: const InputDecoration(labelText: 'WhatsApp / Telefone', prefixIcon: Icon(Icons.phone)),
                    ),
                    const SizedBox(height: 12),
                  ],
                  TextField(
                    controller: emailCtrl,
                    keyboardType: TextInputType.emailAddress,
                    decoration: const InputDecoration(labelText: 'E-mail ou Usuário', prefixIcon: Icon(Icons.email)),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: passCtrl,
                    obscureText: true,
                    decoration: const InputDecoration(labelText: 'Senha', prefixIcon: Icon(Icons.lock)),
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: isLoading
                          ? null
                          : () async {
                              setModalState(() {
                                isLoading = true;
                                errorMessage = null;
                              });

                              final res = isRegister
                                  ? await ApiService.register(
                                      firstName: nameCtrl.text.trim(),
                                      lastName: '',
                                      phone: phoneCtrl.text.trim(),
                                      email: emailCtrl.text.trim(),
                                      password: passCtrl.text.trim(),
                                    )
                                  : await ApiService.login(emailCtrl.text.trim(), passCtrl.text.trim());

                              if (!ctx.mounted) return;
                              if (res.success) {
                                Navigator.pop(ctx);
                                _loadInitialData();
                              } else {
                                setModalState(() {
                                  isLoading = false;
                                  errorMessage = res.message ?? 'Erro ao processar autenticação.';
                                });
                              }
                            },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFD4AF37),
                        foregroundColor: const Color(0xFF121519),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      ),
                      child: isLoading
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF121519)),
                            )
                          : Text(isRegister ? 'Cadastrar e Entrar' : 'Entrar no App', style: const TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Center(
                    child: TextButton(
                      onPressed: () => setModalState(() {
                        isRegister = !isRegister;
                        errorMessage = null;
                      }),
                      child: Text(
                        isRegister ? 'Já tem conta? Entrar' : 'Não tem conta? Cadastre-se grátis',
                        style: const TextStyle(color: Color(0xFF1EA8D7), fontSize: 12, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  void _showAddVehicleModal() {
    final plateCtrl = TextEditingController();
    final brandCtrl = TextEditingController();
    final modelCtrl = TextEditingController();
    final colorCtrl = TextEditingController();
    String vType = 'sedan';

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF1E232A),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(28))),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 24,
                bottom: MediaQuery.of(context).viewInsets.bottom + 24,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Cadastrar Carro na Garagem',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, color: Color(0xFF9A9FA8)),
                        onPressed: () => Navigator.pop(ctx),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  TextField(
                    controller: plateCtrl,
                    textCapitalization: TextCapitalization.characters,
                    decoration: const InputDecoration(labelText: 'Placa (Ex: ABC1D23)', prefixIcon: Icon(Icons.confirmation_number)),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: brandCtrl,
                          decoration: const InputDecoration(labelText: 'Marca (Ex: Toyota)'),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: TextField(
                          controller: modelCtrl,
                          decoration: const InputDecoration(labelText: 'Modelo (Ex: Corolla)'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: colorCtrl,
                    decoration: const InputDecoration(labelText: 'Cor (Ex: Preto)'),
                  ),
                  const SizedBox(height: 18),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () async {
                        if (plateCtrl.text.isNotEmpty && brandCtrl.text.isNotEmpty && modelCtrl.text.isNotEmpty) {
                          final ok = await ApiService.createVehicle(
                            plate: plateCtrl.text.trim(),
                            brand: brandCtrl.text.trim(),
                            model: modelCtrl.text.trim(),
                            color: colorCtrl.text.trim(),
                            vehicleType: vType,
                          );
                          if (!ctx.mounted) return;
                          if (ok) {
                            Navigator.pop(ctx);
                            _loadInitialData();
                          }
                        }
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFD4AF37),
                        foregroundColor: const Color(0xFF121519),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      ),
                      child: const Text('Salvar Veículo', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  void _showBookingModal(ServiceItem service) {
    if (!_isLoggedIn) {
      _showLoginModal();
      return;
    }

    if (_myVehicles.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Por favor, cadastre um veículo na garagem antes de agendar.')),
      );
      _showAddVehicleModal();
      return;
    }

    VehicleItem selectedVehicle = _myVehicles.first;
    DateTime selectedDate = DateTime.now().add(const Duration(days: 1));
    String selectedTime = '10:00';
    final notesCtrl = TextEditingController();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF1E232A),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(28))),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 24,
                bottom: MediaQuery.of(context).viewInsets.bottom + 24,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          'Agendar: ${service.name}',
                          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: Colors.white),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, color: Color(0xFF9A9FA8)),
                        onPressed: () => Navigator.pop(ctx),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  // Seletor de Carro
                  const Text('Selecione o Veículo:', style: TextStyle(fontSize: 12, color: Color(0xFF9A9FA8))),
                  const SizedBox(height: 6),
                  DropdownButtonFormField<VehicleItem>(
                    initialValue: selectedVehicle,
                    dropdownColor: const Color(0xFF14171A),
                    items: _myVehicles.map((v) {
                      return DropdownMenuItem(
                        value: v,
                        child: Text('${v.plate} - ${v.brand} ${v.model}', style: const TextStyle(fontSize: 13, color: Colors.white)),
                      );
                    }).toList(),
                    onChanged: (val) {
                      if (val != null) setModalState(() => selectedVehicle = val);
                    },
                    decoration: InputDecoration(
                      filled: true,
                      fillColor: const Color(0xFF121519),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                  const SizedBox(height: 14),

                  // Data e Hora
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () async {
                            final picked = await showDatePicker(
                              context: context,
                              initialDate: selectedDate,
                              firstDate: DateTime.now(),
                              lastDate: DateTime.now().add(const Duration(days: 60)),
                            );
                            if (picked != null) {
                              setModalState(() => selectedDate = picked);
                            }
                          },
                          icon: const Icon(Icons.calendar_today, size: 16),
                          label: Text(DateFormat('dd/MM/yyyy').format(selectedDate)),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          initialValue: selectedTime,
                          dropdownColor: const Color(0xFF14171A),
                          items: ['08:00', '09:00', '10:00', '11:00', '13:00', '14:00', '15:00', '16:00', '17:00']
                              .map((t) => DropdownMenuItem(value: t, child: Text(t, style: const TextStyle(fontSize: 13, color: Colors.white))))
                              .toList(),
                          onChanged: (val) {
                            if (val != null) setModalState(() => selectedTime = val);
                          },
                          decoration: InputDecoration(
                            filled: true,
                            fillColor: const Color(0xFF121519),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  TextField(
                    controller: notesCtrl,
                    decoration: const InputDecoration(labelText: 'Observações (Opcional)'),
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () async {
                        final messenger = ScaffoldMessenger.of(context);
                        final ok = await ApiService.bookAppointment(
                          companyId: _selectedCompany!.id,
                          vehicleId: selectedVehicle.id,
                          serviceTypeId: service.id,
                          date: DateFormat('yyyy-MM-dd').format(selectedDate),
                          time: selectedTime,
                          notes: notesCtrl.text.trim(),
                        );
                        if (!ctx.mounted) return;
                        if (ok) {
                          Navigator.pop(ctx);
                          messenger.showSnackBar(
                            const SnackBar(content: Text('Agendamento realizado com sucesso!')),
                          );
                          _loadInitialData();
                          _backToGlobalNetwork(4); // Vai para aba de agendamentos
                        }
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFD4AF37),
                        foregroundColor: const Color(0xFF121519),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      ),
                      child: const Text('Confirmar Agendamento VIP', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  void _showPhotoZoom(String url, String caption) {
    showDialog(
      context: context,
      builder: (ctx) {
        return Dialog(
          backgroundColor: Colors.transparent,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: InteractiveViewer(
                  child: CachedNetworkImage(
                    imageUrl: url,
                    fit: BoxFit.contain,
                  ),
                ),
              ),
              if (caption.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(caption, style: const TextStyle(color: Colors.white, fontSize: 12)),
              ],
            ],
          ),
        );
      },
    );
  }

  void _confirmDeleteVehicle(VehicleItem vehicle) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E232A),
        title: const Text('Remover Veículo', style: TextStyle(color: Colors.white)),
        content: Text('Deseja realmente remover o veículo ${vehicle.plate} da sua garagem?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              await ApiService.deleteVehicle(vehicle.id);
              _loadInitialData();
            },
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFEF4444)),
            child: const Text('Remover', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  void _confirmCancelAppointment(AppointmentItem appt) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E232A),
        title: const Text('Cancelar Agendamento', style: TextStyle(color: Colors.white)),
        content: Text('Deseja realmente cancelar seu agendamento de ${appt.serviceName} em ${appt.scheduledDate}?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Não')),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              await ApiService.cancelAppointment(appt.id);
              _loadInitialData();
            },
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFEF4444)),
            child: const Text('Sim, Cancelar', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}
