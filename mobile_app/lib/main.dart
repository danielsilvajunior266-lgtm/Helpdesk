import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'core/models.dart';
import 'core/api_service.dart';

void main() {
  runApp(const AutoFlowApp());
}

class AutoFlowApp extends StatelessWidget {
  const AutoFlowApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AutoFlow Mobile - Estética Automotiva Premium',
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
  int _currentIndex = 0;
  List<Company> _companies = [];
  Company? _selectedCompany;
  List<ServiceItem> _services = [];
  List<ServiceOrderItem> _orders = [];
  List<VehicleItem> _myVehicles = [];
  LoyaltyBalance? _loyalty;
  bool _isLoading = true;
  bool _isLoggedIn = false;
  bool _isSelectingCompany = true;
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Company? get _recentCompany {
    if (_orders.isNotEmpty) {
      final firstOrder = _orders.first;
      // Procura a empresa da última ordem na lista de empresas
      for (final c in _companies) {
        if (c.name.toLowerCase() == firstOrder.companyName.toLowerCase() || c.id == firstOrder.id) {
          return c;
        }
      }
    }
    return _selectedCompany ?? (_companies.isNotEmpty ? _companies.first : null);
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoading = true);
    final loggedIn = await ApiService.isLoggedIn();
    final companies = await ApiService.getCompanies();
    List<ServiceOrderItem> orders = [];
    List<VehicleItem> myVehicles = [];
    if (loggedIn) {
      orders = await ApiService.getMyOrders();
      myVehicles = await ApiService.getMyVehicles();
    }

    if (companies.isNotEmpty) {
      _selectedCompany = companies.first;
      final services = await ApiService.getServices(_selectedCompany!.id);
      setState(() {
        _companies = companies;
        _services = services;
        _orders = orders;
        _myVehicles = myVehicles;
        _isLoggedIn = loggedIn;
        _isLoading = false;
      });
      _loadCompanyDetails();
    } else {
      setState(() {
        _companies = [];
        _orders = orders;
        _myVehicles = myVehicles;
        _isLoggedIn = loggedIn;
        _isLoading = false;
      });
    }
  }

  Future<void> _loadCompanyDetails() async {
    if (_selectedCompany == null) return;
    final services = await ApiService.getServices(_selectedCompany!.id);
    final orders = await ApiService.getMyOrders();
    final loggedIn = await ApiService.isLoggedIn();
    List<VehicleItem> myVehicles = [];
    if (loggedIn) {
      myVehicles = await ApiService.getMyVehicles();
    }
    LoyaltyBalance? loyalty;
    if (_selectedCompany!.features.hasLoyalty) {
      loyalty = await ApiService.getLoyaltyBalance(_selectedCompany!.id);
    }

    setState(() {
      _services = services;
      _orders = orders;
      _myVehicles = myVehicles;
      _loyalty = loyalty;
      _isLoggedIn = loggedIn;
    });
  }

  void _selectCompany(Company company) {
    setState(() {
      _selectedCompany = company;
      _isSelectingCompany = false;
      _currentIndex = 0;
    });
    _loadCompanyDetails();
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

    // Adaptive Device Detection: checks window/screen constraints
    final isTablet = MediaQuery.sizeOf(context).width >= 600;

    if (_companies.isEmpty) {
      return Scaffold(
        backgroundColor: const Color(0xFF121519),
        appBar: AppBar(
          backgroundColor: const Color(0xFF14171A),
          title: const Text('AutoFlow Mobile'),
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 48, color: Color(0xFFEF4444)),
                const SizedBox(height: 16),
                const Text(
                  'Não foi possível conectar ao servidor',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Verifique se a API backend Django está em execução.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 13, color: Color(0xFF9A9FA8)),
                ),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: _loadInitialData,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Tentar Novamente'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFD4AF37),
                    foregroundColor: const Color(0xFF121519),
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    if (_isSelectingCompany || _selectedCompany == null) {
      return _buildCompanySelectScreen(isTablet);
    }

    final hasLoyalty = _selectedCompany?.features.hasLoyalty ?? false;

    final List<Widget> pages = [
      _buildServicesTab(isTablet),
      _buildOrdersTrackingTab(isTablet),
      if (hasLoyalty) _buildLoyaltyTab(isTablet),
      _buildGarageTab(isTablet),
      _buildAboutTab(isTablet),
    ];

    final List<NavigationDestination> destinations = [
      const NavigationDestination(
        icon: Icon(Icons.cleaning_services_outlined, color: Color(0xFFD4AF37)),
        selectedIcon: Icon(Icons.cleaning_services, color: Color(0xFF1EA8D7)),
        label: 'Catálogo',
      ),
      const NavigationDestination(
        icon: Icon(Icons.directions_car_outlined, color: Color(0xFFD4AF37)),
        selectedIcon: Icon(Icons.directions_car, color: Color(0xFF1EA8D7)),
        label: 'Meu Carro',
      ),
      if (hasLoyalty)
        const NavigationDestination(
          icon: Icon(Icons.stars_outlined, color: Color(0xFFD4AF37)),
          selectedIcon: Icon(Icons.stars, color: Color(0xFF1EA8D7)),
          label: 'Fidelidade',
        ),
      const NavigationDestination(
        icon: Icon(Icons.key_outlined, color: Color(0xFFD4AF37)),
        selectedIcon: Icon(Icons.key, color: Color(0xFF1EA8D7)),
        label: 'Garagem',
      ),
      const NavigationDestination(
        icon: Icon(Icons.info_outline, color: Color(0xFFD4AF37)),
        selectedIcon: Icon(Icons.info, color: Color(0xFF1EA8D7)),
        label: 'Sobre',
      ),
    ];

    if (_currentIndex >= pages.length) {
      _currentIndex = 0;
    }

    // TABLET / DESKTOP LAYOUT (>= 600px)
    if (isTablet) {
      return Scaffold(
        backgroundColor: const Color(0xFF121519),
        body: Row(
          children: [
            // Side NavigationRail
            NavigationRail(
              backgroundColor: const Color(0xFF14171A),
              selectedIndex: _currentIndex,
              onDestinationSelected: (index) => setState(() => _currentIndex = index),
              labelType: NavigationRailLabelType.all,
              leading: Column(
                children: [
                  const SizedBox(height: 16),
                  InkWell(
                    onTap: () => setState(() => _isSelectingCompany = true),
                    borderRadius: BorderRadius.circular(16),
                    child: Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        color: const Color(0xFF121519),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.5)),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFFD4AF37).withValues(alpha: 0.25),
                            blurRadius: 10,
                          ),
                        ],
                      ),
                      padding: const EdgeInsets.all(4),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: (_selectedCompany?.logo != null && _selectedCompany!.logo!.isNotEmpty)
                            ? Image.network(
                                _selectedCompany!.logo!,
                                fit: BoxFit.contain,
                                errorBuilder: (context, error, stackTrace) => Image.asset('assets/images/logo.png', fit: BoxFit.contain),
                              )
                            : Image.asset(
                                'assets/images/logo.png',
                                fit: BoxFit.contain,
                                errorBuilder: (context, error, stackTrace) => const Icon(Icons.auto_awesome, color: Color(0xFFD4AF37), size: 24),
                              ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _selectedCompany?.name ?? 'AutoFlow',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: Colors.white),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 4),
                  InkWell(
                    onTap: () => setState(() => _isSelectingCompany = true),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E232A),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.3)),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.swap_horiz, size: 12, color: Color(0xFFD4AF37)),
                          SizedBox(width: 3),
                          Text('Trocar', style: TextStyle(fontSize: 10, color: Color(0xFFD4AF37), fontWeight: FontWeight.bold)),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
              ),
              trailing: Expanded(
                child: Align(
                  alignment: Alignment.bottomCenter,
                  child: Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: IconButton(
                      icon: Icon(
                        _isLoggedIn ? Icons.account_circle : Icons.login,
                        color: _isLoggedIn ? const Color(0xFFD4AF37) : const Color(0xFF94A3B8),
                      ),
                      tooltip: _isLoggedIn ? 'Conta Conectada (Sair)' : 'Entrar / Login',
                      onPressed: () {
                        if (_isLoggedIn) {
                          _showLogoutConfirmDialog();
                        } else {
                          _showLoginModal();
                        }
                      },
                    ),
                  ),
                ),
              ),
              destinations: destinations.map((d) => NavigationRailDestination(
                icon: d.icon,
                selectedIcon: d.selectedIcon ?? d.icon,
                label: Text(d.label, style: const TextStyle(fontSize: 11)),
              )).toList(),
            ),
            VerticalDivider(width: 1, thickness: 1, color: const Color(0xFFA3734C).withValues(alpha: 0.25)),
            // Main Content Area with Adaptive Animations
            Expanded(
              child: Scaffold(
                backgroundColor: const Color(0xFF121519),
                appBar: AppBar(
                  backgroundColor: const Color(0xFF14171A),
                  elevation: 0,
                  title: Text(
                    destinations[_currentIndex].label,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  actions: [
                    Container(
                      margin: const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E232A),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.3)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.star, size: 14, color: Color(0xFFD4AF37)),
                          const SizedBox(width: 6),
                          Text(
                            'VIP Mode • ${_selectedCompany?.name}',
                            style: const TextStyle(fontSize: 11, color: Color(0xFFF5E6BE), fontWeight: FontWeight.w600),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                body: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 960),
                    child: _buildAdaptiveAnimatedPage(
                      isTablet: true,
                      child: pages[_currentIndex],
                      index: _currentIndex,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      );
    }

    // MOBILE PHONE LAYOUT (< 600px)
    return Scaffold(
      backgroundColor: const Color(0xFF121519),
      appBar: AppBar(
        backgroundColor: const Color(0xFF14171A),
        elevation: 0,
        title: InkWell(
          onTap: () => setState(() => _isSelectingCompany = true),
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 4),
            child: Row(
              children: [
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    color: const Color(0xFF121519),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.4)),
                  ),
                  padding: const EdgeInsets.all(2),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: (_selectedCompany?.logo != null && _selectedCompany!.logo!.isNotEmpty)
                        ? Image.network(
                            _selectedCompany!.logo!,
                            fit: BoxFit.contain,
                            errorBuilder: (context, error, stackTrace) => Image.asset('assets/images/logo.png', fit: BoxFit.contain),
                          )
                        : Image.asset(
                            'assets/images/logo.png',
                            fit: BoxFit.contain,
                            errorBuilder: (context, error, stackTrace) => const Icon(Icons.auto_awesome, color: Color(0xFFD4AF37), size: 18),
                          ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Flexible(
                            child: Text(
                              _selectedCompany?.name ?? 'AutoFlow',
                              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 4),
                          const Text('★★★★★', style: TextStyle(color: Color(0xFFD4AF37), fontSize: 9)),
                        ],
                      ),
                      const Text(
                        'Estética Automotiva • Unidade VIP',
                        style: TextStyle(
                          fontSize: 10,
                          color: Color(0xFFD4AF37),
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.storefront, color: Color(0xFFD4AF37)),
            tooltip: 'Trocar Lava-Jato',
            onPressed: () => setState(() => _isSelectingCompany = true),
          ),
          IconButton(
            icon: Icon(
              _isLoggedIn ? Icons.account_circle : Icons.login,
              color: _isLoggedIn ? const Color(0xFFD4AF37) : const Color(0xFF94A3B8),
            ),
            tooltip: _isLoggedIn ? 'Conta Conectada' : 'Entrar / Login',
            onPressed: () {
              if (_isLoggedIn) {
                _showLogoutConfirmDialog();
              } else {
                _showLoginModal();
              }
            },
          ),
        ],
      ),
      body: _buildAdaptiveAnimatedPage(
        isTablet: false,
        child: pages[_currentIndex],
        index: _currentIndex,
      ),
      bottomNavigationBar: NavigationBar(
        backgroundColor: const Color(0xFF14171A),
        indicatorColor: const Color(0xFF1EA8D7).withValues(alpha: 0.22),
        elevation: 8,
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() => _currentIndex = index);
        },
        destinations: destinations,
      ),
    );
  }

  // Adaptive Animated Page Switcher with Device-tailored transitions
  Widget _buildAdaptiveAnimatedPage({
    required bool isTablet,
    required Widget child,
    required int index,
  }) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 300),
      switchInCurve: Curves.easeOutCubic,
      switchOutCurve: Curves.easeInCubic,
      transitionBuilder: (Widget pageChild, Animation<double> animation) {
        if (isTablet) {
          // Transição refinada para Tablet: CrossFade + Leve Escala
          return FadeTransition(
            opacity: animation,
            child: ScaleTransition(
              scale: Tween<double>(begin: 0.98, end: 1.0).animate(animation),
              child: pageChild,
            ),
          );
        } else {
          // Transição nativa para Mobile: Slide Horizontal Suave + Fade
          return SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0.04, 0),
              end: Offset.zero,
            ).animate(animation),
            child: FadeTransition(
              opacity: animation,
              child: pageChild,
            ),
          );
        }
      },
      child: KeyedSubtree(
        key: ValueKey<int>(index),
        child: child,
      ),
    );
  }

  // SCREEN: SELEÇÃO DE EMPRESA / LAVA-JATO (Apresentada logo no início)
  Widget _buildCompanySelectScreen(bool isTablet) {
    final recent = _recentCompany;
    final recentOrder = _orders.isNotEmpty ? _orders.first : null;
    final filteredCompanies = _companies.where((c) {
      if (_searchQuery.isEmpty) return true;
      final q = _searchQuery.toLowerCase();
      return c.name.toLowerCase().contains(q) ||
          c.address.toLowerCase().contains(q) ||
          c.city.toLowerCase().contains(q);
    }).toList();

    return Scaffold(
      backgroundColor: const Color(0xFF121519),
      appBar: AppBar(
        backgroundColor: const Color(0xFF14171A),
        elevation: 0,
        title: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: const Color(0xFF121519),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.4)),
              ),
              padding: const EdgeInsets.all(2),
              child: Image.asset(
                'assets/images/logo.png',
                fit: BoxFit.contain,
                errorBuilder: (context, error, stackTrace) => const Icon(Icons.auto_awesome, color: Color(0xFFD4AF37), size: 18),
              ),
            ),
            const SizedBox(width: 10),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'AutoFlow',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                Text(
                  'Estética Automotiva',
                  style: TextStyle(fontSize: 10, color: Color(0xFFD4AF37), fontWeight: FontWeight.w700),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(
              _isLoggedIn ? Icons.account_circle : Icons.login,
              color: _isLoggedIn ? const Color(0xFFF59E0B) : const Color(0xFF94A3B8),
            ),
            tooltip: _isLoggedIn ? 'Conta Conectada' : 'Entrar / Login',
            onPressed: () {
              if (_isLoggedIn) {
                _showLogoutConfirmDialog();
              } else {
                _showLoginModal();
              }
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadInitialData,
        color: const Color(0xFFF59E0B),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Header / Greeting Icon Showcase
            Container(
              alignment: Alignment.center,
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Column(
                children: [
                  Container(
                    width: 90,
                    height: 90,
                    margin: const EdgeInsets.only(bottom: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF121519),
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.5)),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFFD4AF37).withValues(alpha: 0.3),
                          blurRadius: 18,
                        ),
                      ],
                    ),
                    padding: const EdgeInsets.all(6),
                    child: Image.asset(
                      'assets/images/logo.png',
                      fit: BoxFit.contain,
                      errorBuilder: (context, error, stackTrace) => const Icon(Icons.local_car_wash, color: Color(0xFFD4AF37), size: 38),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF59E0B).withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: const Color(0xFFF59E0B).withValues(alpha: 0.35)),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.star, color: Color(0xFFF59E0B), size: 14),
                        SizedBox(width: 6),
                        Text(
                          'Rede Credenciada VIP ★★★★★',
                          style: TextStyle(color: Color(0xFFF59E0B), fontSize: 11, fontWeight: FontWeight.w800),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Onde vamos cuidar do seu veículo hoje?',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: Colors.white, height: 1.2),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Selecione o centro de estética credenciado para agendar serviços com padrão de excelência 5 estrelas.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // Search Bar
            TextField(
              controller: _searchController,
              onChanged: (val) => setState(() => _searchQuery = val),
              style: const TextStyle(color: Colors.white, fontSize: 14),
              decoration: InputDecoration(
                hintText: 'Pesquisar por nome, cidade ou bairro...',
                hintStyle: const TextStyle(color: Color(0xFF64748B), fontSize: 13),
                prefixIcon: const Icon(Icons.search, color: Color(0xFFF59E0B), size: 20),
                suffixIcon: _searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.close, color: Color(0xFF94A3B8), size: 18),
                        onPressed: () {
                          _searchController.clear();
                          setState(() => _searchQuery = '');
                        },
                      )
                    : null,
                filled: true,
                fillColor: const Color(0xFF0F172A),
                contentPadding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.1)),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.1)),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: const BorderSide(color: Color(0xFF3B82F6), width: 1.5),
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Card: Último Lava-Jato que você foi
            if (recent != null && _searchQuery.isEmpty) ...[
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      const Color(0xFFF59E0B).withValues(alpha: 0.15),
                      const Color(0xFF0F172A),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: const Color(0xFFF59E0B).withValues(alpha: 0.35)),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFFF59E0B).withValues(alpha: 0.1),
                      blurRadius: 20,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF59E0B).withValues(alpha: 0.2),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: const Color(0xFFF59E0B).withValues(alpha: 0.4)),
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.history, color: Color(0xFFFBBF24), size: 14),
                              SizedBox(width: 4),
                              Text(
                                'ÚLTIMO LAVA-JATO VISITADO',
                                style: TextStyle(
                                  color: Color(0xFFFBBF24),
                                  fontSize: 10,
                                  fontWeight: FontWeight.w900,
                                  letterSpacing: 0.5,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const Spacer(),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: const Color(0xFFD4AF37).withValues(alpha: 0.2),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.4)),
                          ),
                          child: const Text(
                            'VIP',
                            style: TextStyle(color: Color(0xFFF5E6BE), fontSize: 10, fontWeight: FontWeight.w900),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      recent.name,
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        const Icon(Icons.location_on, color: Color(0xFFFBBF24), size: 14),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            recent.address.isNotEmpty ? recent.address : 'São Paulo, SP',
                            style: const TextStyle(fontSize: 12, color: Color(0xFFCBD5E1)),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                    if (recentOrder != null) ...[
                      const SizedBox(height: 10),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: const Color(0xFF090D16).withValues(alpha: 0.6),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.check_circle_outline, color: Color(0xFFFBBF24), size: 16),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                'Último serviço: ${recentOrder.serviceName} (${recentOrder.vehiclePlate})',
                                style: const TextStyle(fontSize: 11, color: Color(0xFFE2E8F0), fontWeight: FontWeight.w500),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                    const SizedBox(height: 14),
                    SizedBox(
                      width: double.infinity,
                      height: 44,
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFF59E0B),
                          foregroundColor: const Color(0xFF090D16),
                          elevation: 4,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                        ),
                        onPressed: () => _selectCompany(recent),
                        icon: const Icon(Icons.arrow_forward, size: 18),
                        label: const Text(
                          'Desejo ir neste novamente',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
            ],

            // Lista de Todas as Unidades Credenciadas
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Row(
                  children: [
                    Icon(Icons.storefront, color: Color(0xFF60A5FA), size: 18),
                    SizedBox(width: 6),
                    Text(
                      'Lava-Jatos Credenciados',
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                  ],
                ),
                Text(
                  '${filteredCompanies.length} unidades',
                  style: const TextStyle(fontSize: 11, color: Color(0xFF94A3B8), fontWeight: FontWeight.w600),
                ),
              ],
            ),

            const SizedBox(height: 12),

            if (filteredCompanies.isEmpty)
              Container(
                padding: const EdgeInsets.symmetric(vertical: 36, horizontal: 16),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: const Color(0xFF0F172A),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
                ),
                child: Column(
                  children: [
                    const Icon(Icons.search_off, size: 48, color: Color(0xFF64748B)),
                    const SizedBox(height: 12),
                    const Text(
                      'Nenhum lava-jato encontrado',
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Tente buscar por outros termos ou cidades.',
                      style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                    ),
                    const SizedBox(height: 12),
                    TextButton(
                      onPressed: () {
                        _searchController.clear();
                        setState(() => _searchQuery = '');
                      },
                      child: const Text('Limpar busca', style: TextStyle(color: Color(0xFF3B82F6))),
                    ),
                  ],
                ),
              )
            else if (isTablet)
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 14,
                  mainAxisSpacing: 14,
                  mainAxisExtent: 210,
                ),
                itemCount: filteredCompanies.length,
                itemBuilder: (context, index) {
                  return _buildCompanyCard(filteredCompanies[index]);
                },
              )
            else
              ...filteredCompanies.map((c) => _buildCompanyCard(c)),
          ],
        ),
      ),
    );
  }

  Widget _buildCompanyCard(Company c) {
    final isCurrent = _selectedCompany?.id == c.id;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E232A),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isCurrent
              ? const Color(0xFF1EA8D7)
              : const Color(0xFFA3734C).withValues(alpha: 0.3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 44,
                height: 44,
                padding: const EdgeInsets.all(3),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [
                      Color(0xFF121519),
                      Color(0xFF1E232A),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.4)),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: (c.logo != null && c.logo!.isNotEmpty)
                      ? Image.network(
                          c.logo!,
                          fit: BoxFit.contain,
                          errorBuilder: (context, error, stackTrace) => Center(
                            child: Text(
                              c.name.isNotEmpty ? c.name.substring(0, c.name.length >= 2 ? 2 : 1).toUpperCase() : 'LJ',
                              style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFFD4AF37), fontSize: 14),
                            ),
                          ),
                        )
                      : Center(
                          child: Text(
                            c.name.isNotEmpty ? c.name.substring(0, c.name.length >= 2 ? 2 : 1).toUpperCase() : 'LJ',
                            style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFFD4AF37), fontSize: 14),
                          ),
                        ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      c.name,
                      style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        const Icon(Icons.location_on, color: Color(0xFFD4AF37), size: 12),
                        const SizedBox(width: 3),
                        Expanded(
                          child: Text(
                            c.address.isNotEmpty ? c.address : 'São Paulo, SP',
                            style: const TextStyle(fontSize: 11, color: Color(0xFF9A9FA8)),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFFD4AF37).withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.35)),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.verified, size: 10, color: Color(0xFFD4AF37)),
                    SizedBox(width: 3),
                    Text(
                      'CREDENCIADO',
                      style: TextStyle(
                        fontSize: 9,
                        fontWeight: FontWeight.w800,
                        color: Color(0xFFF5E6BE),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              _buildFeatureBadge('Agendamento', Icons.calendar_today, const Color(0xFF1EA8D7)),
              _buildFeatureBadge('Fotos Antes & Depois', Icons.camera_alt, const Color(0xFFA3734C)),
              if (c.features.hasLoyalty)
                _buildFeatureBadge('Fidelidade', Icons.card_giftcard, const Color(0xFFD4AF37)),
            ],
          ),
          const Spacer(),
          SizedBox(
            width: double.infinity,
            height: 40,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFD4AF37),
                foregroundColor: const Color(0xFF121519),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                elevation: 0,
              ),
              onPressed: () => _selectCompany(c),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text('Selecionar este Lava-Jato', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                  SizedBox(width: 4),
                  Icon(Icons.chevron_right, size: 16),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeatureBadge(String label, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.25)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 11),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  // TAB 1: Catálogo de Serviços
  Widget _buildServicesTab(bool isTablet) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF1E232A), Color(0xFF121519)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.35)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.4),
                blurRadius: 16,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.location_on, size: 16, color: Color(0xFF1EA8D7)),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      _selectedCompany?.address ?? 'São Paulo, SP',
                      style: const TextStyle(fontSize: 12, color: Color(0xFF9A9FA8)),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                _selectedCompany?.name ?? '',
                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: Colors.white),
              ),
              const SizedBox(height: 4),
              const Text(
                'Agende ou acompanhe seu serviço em tempo real com garantia VIP!',
                style: TextStyle(fontSize: 12, color: Color(0xFFD4AF37), fontWeight: FontWeight.w600),
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),

        // Quick Category Showcase
        const Text(
          'Especialidades de Estética',
          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
        ),
        const SizedBox(height: 10),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              _buildCategoryPill('Polimento Técnico', Icons.auto_awesome, const Color(0xFFD4AF37)),
              const SizedBox(width: 8),
              _buildCategoryPill('Lavagem Detalhada', Icons.local_car_wash, const Color(0xFF1EA8D7)),
              const SizedBox(width: 8),
              _buildCategoryPill('Vitrificação 9H', Icons.shield, const Color(0xFFA3734C)),
              const SizedBox(width: 8),
              _buildCategoryPill('Higienização Interna', Icons.cleaning_services, const Color(0xFF10B981)),
            ],
          ),
        ),

        const SizedBox(height: 24),
        const Text(
          'Serviços Disponíveis',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
        ),
        const SizedBox(height: 12),

        if (isTablet)
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              mainAxisExtent: 100,
            ),
            itemCount: _services.length,
            itemBuilder: (context, index) {
              return _buildServiceCard(_services[index]);
            },
          )
        else
          ..._services.map((service) => _buildServiceCard(service)),
      ],
    );
  }

  Widget _buildCategoryPill(String title, IconData icon, Color accentColor) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xFF1E232A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: accentColor.withValues(alpha: 0.35)),
        boxShadow: [
          BoxShadow(
            color: accentColor.withValues(alpha: 0.1),
            blurRadius: 8,
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: accentColor, size: 16),
          const SizedBox(width: 8),
          Text(
            title,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Color(0xFFF5F5F7)),
          ),
        ],
      ),
    );
  }

  IconData _getServiceIcon(String name) {
    final lower = name.toLowerCase();
    if (lower.contains('polimento') || lower.contains('cristaliz') || lower.contains('vitrific')) {
      return Icons.auto_awesome;
    }
    if (lower.contains('roda') || lower.contains('aro') || lower.contains('freio')) {
      return Icons.trip_origin;
    }
    if (lower.contains('pneu') || lower.contains('borracha') || lower.contains('pretinho')) {
      return Icons.album;
    }
    if (lower.contains('pad') || lower.contains('boina') || lower.contains('cera') || lower.contains('selante')) {
      return Icons.cleaning_services;
    }
    if (lower.contains('detalhe') || lower.contains('detalhamento') || lower.contains('motor') || lower.contains('farol')) {
      return Icons.build_circle;
    }
    if (lower.contains('pano') || lower.contains('microfibra') || lower.contains('banco') || lower.contains('couro') || lower.contains('higieniza')) {
      return Icons.airline_seat_recline_extra;
    }
    return Icons.local_car_wash;
  }

  Widget _buildServiceCard(ServiceItem service) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E232A),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.3)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.35),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF2A313C), Color(0xFF181D23)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.45)),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFFD4AF37).withValues(alpha: 0.15),
                  blurRadius: 8,
                ),
              ],
            ),
            child: Center(
              child: Icon(_getServiceIcon(service.name), color: const Color(0xFFD4AF37), size: 24),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  service.name,
                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  '~${service.durationMinutes} minutos',
                  style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                ),
                if (service.loyaltyPoints > 0 && (_selectedCompany?.features.hasLoyalty ?? false))
                  Text(
                    '+${service.loyaltyPoints} pts fidelidade',
                    style: const TextStyle(fontSize: 11, color: Color(0xFFF59E0B), fontWeight: FontWeight.w600),
                  ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                'R\$ ${service.price.toStringAsFixed(2)}',
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: Color(0xFF10B981)),
              ),
              const SizedBox(height: 4),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFF59E0B),
                  foregroundColor: const Color(0xFF070B13),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  minimumSize: Size.zero,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                onPressed: () => _showBookingDialog(service),
                child: const Text('Agendar', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // TAB 2: Acompanhamento de Pátio com Vistoria Antes/Depois
  Widget _buildOrdersTrackingTab(bool isTablet) {
    final hasInspections = _selectedCompany?.features.hasInspections ?? false;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF0F172A),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: const Color(0xFF1E293B)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.garage, color: Color(0xFF10B981)),
                      SizedBox(width: 8),
                      Text('Veículo em Atendimento', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  if (_orders.isNotEmpty)
                    Text('${_orders.length} ordens', style: const TextStyle(fontSize: 11, color: Color(0xFF64748B))),
                ],
              ),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFF090D16),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF2563EB).withValues(alpha: 0.3)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: const Color(0xFF1E293B),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            _orders.isNotEmpty ? _orders.first.vehiclePlate : 'VIP3B33',
                            style: const TextStyle(fontFamily: 'monospace', fontWeight: FontWeight.bold, fontSize: 13),
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          _orders.isNotEmpty ? _orders.first.serviceName : 'BMW 320i M Sport',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                        Text(
                          _orders.isNotEmpty ? 'R\$ ${_orders.first.finalPrice.toStringAsFixed(2)}' : 'Polimento Técnico',
                          style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: const Color(0xFF3B82F6).withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.sync, size: 14, color: Color(0xFF60A5FA)),
                          const SizedBox(width: 4),
                          Text(
                            _orders.isNotEmpty ? _orders.first.statusLabel : 'Em Lavagem',
                            style: const TextStyle(fontSize: 11, color: Color(0xFF60A5FA), fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),

        if (hasInspections) ...[
          const Row(
            children: [
              Icon(Icons.camera_alt, size: 18, color: Color(0xFF8B5CF6)),
              SizedBox(width: 8),
              Text('Vistoria Fotográfica (Antes & Depois)', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: Container(
                  height: isTablet ? 220 : 160,
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F172A),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFF1E293B)),
                  ),
                  child: const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.photo, color: Color(0xFFF59E0B), size: 36),
                        SizedBox(height: 6),
                        Text('Foto Entrada (Antes)', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                        Text('Registrada no Pátio', style: TextStyle(fontSize: 10, color: Color(0xFF64748B))),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Container(
                  height: isTablet ? 220 : 160,
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F172A),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFF1E293B)),
                  ),
                  child: const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.auto_awesome, color: Color(0xFF10B981), size: 36),
                        SizedBox(height: 6),
                        Text('Foto Entrega (Depois)', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                        Text('Pós Detalhamento VIP', style: TextStyle(fontSize: 10, color: Color(0xFF64748B))),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ] else ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF0F172A),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFF1E293B)),
            ),
            child: const Row(
              children: [
                Icon(Icons.lock_outline, color: Color(0xFF64748B)),
                SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Fotos de vistoria em tempo real disponíveis para lava-jatos com plano Premium.',
                    style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  // TAB 3: Clube Fidelidade
  Widget _buildLoyaltyTab(bool isTablet) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF831843), Color(0xFF0F172A)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: const Color(0xFFEC4899).withValues(alpha: 0.3)),
          ),
          child: Column(
            children: [
              const Icon(Icons.stars, size: 52, color: Color(0xFFF59E0B)),
              const SizedBox(height: 12),
              const Text(
                'Saldo Disponível',
                style: TextStyle(fontSize: 13, color: Color(0xFFFBCFE8)),
              ),
              const SizedBox(height: 4),
              Text(
                '${_loyalty?.pointsBalance ?? 35} pts',
                style: const TextStyle(fontSize: 36, fontWeight: FontWeight.w900, color: Colors.white),
              ),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.black.withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  'Próximo prêmio em ${_loyalty?.pointsNeeded ?? 100} pts',
                  style: const TextStyle(fontSize: 11, color: Color(0xFFFBCFE8)),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        const Text(
          'Recompensa Atual',
          style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF0F172A),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: const Color(0xFF1E293B)),
          ),
          child: Row(
            children: [
              const Icon(Icons.stars, color: Color(0xFFF59E0B), size: 30),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _loyalty?.rewardDescription ?? 'Cristalização de Para-brisa Grátis',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                    const Text('Ao atingir 100 pontos', style: TextStyle(fontSize: 12, color: Color(0xFF64748B))),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // TAB: Garagem VIP (Cadastro e Gestão de Veículos)
  Widget _buildGarageTab(bool isTablet) {
    if (!_isLoggedIn) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: const Color(0xFF1E232A),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.35)),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    color: const Color(0xFF121519),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.5)),
                  ),
                  child: const Icon(Icons.key, color: Color(0xFFD4AF37), size: 30),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Identificação Necessária',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Faça login para cadastrar seus veículos e gerenciar sua garagem com padrão VIP.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 13, color: Color(0xFF9A9FA8)),
                ),
                const SizedBox(height: 20),
                ElevatedButton.icon(
                  onPressed: _showLoginModal,
                  icon: const Icon(Icons.login, size: 18),
                  label: const Text('Entrar na Minha Conta'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFD4AF37),
                    foregroundColor: const Color(0xFF121519),
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Header de Garagem
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: const Color(0xFF1E232A),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.35)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Row(
                children: [
                  Icon(Icons.key, color: Color(0xFFD4AF37), size: 22),
                  SizedBox(width: 10),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Minha Garagem VIP', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                      Text('Veículos salvos para agendamento express', style: TextStyle(fontSize: 11, color: Color(0xFF9A9FA8))),
                    ],
                  ),
                ],
              ),
              ElevatedButton.icon(
                onPressed: () => _showAddVehicleDialog(),
                icon: const Icon(Icons.add, size: 16),
                label: const Text('Cadastrar', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFD4AF37),
                  foregroundColor: const Color(0xFF121519),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        if (_myVehicles.isEmpty)
          Container(
            padding: const EdgeInsets.symmetric(vertical: 36, horizontal: 20),
            decoration: BoxDecoration(
              color: const Color(0xFF14171A),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.2)),
            ),
            child: Column(
              children: [
                const Icon(Icons.directions_car_outlined, size: 48, color: Color(0xFF9A9FA8)),
                const SizedBox(height: 12),
                const Text(
                  'Nenhum veículo cadastrado',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Adicione a placa e modelo do seu veículo para agendamentos em 1 clique.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 12, color: Color(0xFF9A9FA8)),
                ),
                const SizedBox(height: 18),
                ElevatedButton.icon(
                  onPressed: () => _showAddVehicleDialog(),
                  icon: const Icon(Icons.add_circle_outline, size: 18),
                  label: const Text('Cadastrar Primeiro Veículo'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFD4AF37),
                    foregroundColor: const Color(0xFF121519),
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  ),
                ),
              ],
            ),
          )
        else
          ..._myVehicles.map((vehicle) {
            return Container(
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF1E232A),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.3)),
              ),
              child: Row(
                children: [
                  Container(
                    width: 50,
                    height: 50,
                    decoration: BoxDecoration(
                      color: const Color(0xFF121519),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.4)),
                    ),
                    child: const Icon(Icons.directions_car, color: Color(0xFFD4AF37), size: 26),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: const Color(0xFF121519),
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.4)),
                              ),
                              child: Text(
                                vehicle.plate,
                                style: const TextStyle(
                                  color: Color(0xFFD4AF37),
                                  fontFamily: 'monospace',
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              vehicle.vehicleType.toUpperCase(),
                              style: const TextStyle(fontSize: 10, color: Color(0xFF1EA8D7), fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${vehicle.brand} ${vehicle.model}',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                        ),
                        Text(
                          'Cor: ${vehicle.color.isNotEmpty ? vehicle.color : "Padrão"}',
                          style: const TextStyle(fontSize: 11, color: Color(0xFF9A9FA8)),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.calendar_today, color: Color(0xFF1EA8D7), size: 20),
                    tooltip: 'Agendar com este carro',
                    onPressed: () {
                      setState(() => _currentIndex = 0); // Vai para catálogo
                    },
                  ),
                ],
              ),
            );
          }),
      ],
    );
  }

  Future<void> _showAddVehicleDialog({VoidCallback? onAdded}) async {
    if (!_isLoggedIn) {
      _showLoginModal();
      return;
    }

    final plateController = TextEditingController();
    final brandController = TextEditingController();
    final modelController = TextEditingController();
    final colorController = TextEditingController();
    String vehicleType = 'sedan';
    bool isSaving = false;

    await _showAdaptiveModal(
      context: context,
      builder: (modalContext) {
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
                      const Row(
                        children: [
                          Icon(Icons.add_circle, color: Color(0xFFD4AF37), size: 22),
                          SizedBox(width: 8),
                          Text(
                            'Cadastrar Novo Veículo',
                            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                        ],
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, color: Color(0xFF9A9FA8)),
                        onPressed: () => Navigator.pop(context),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: plateController,
                          textCapitalization: TextCapitalization.characters,
                          style: const TextStyle(color: Colors.white, fontSize: 13, fontFamily: 'monospace', fontWeight: FontWeight.bold),
                          decoration: InputDecoration(
                            labelText: 'Placa *',
                            labelStyle: const TextStyle(color: Color(0xFFF5E6BE), fontSize: 12),
                            hintText: 'ABC1D23',
                            hintStyle: const TextStyle(color: Color(0xFF64748B), fontSize: 12),
                            filled: true,
                            fillColor: const Color(0xFF121519),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: TextField(
                          controller: brandController,
                          style: const TextStyle(color: Colors.white, fontSize: 13),
                          decoration: InputDecoration(
                            labelText: 'Marca *',
                            labelStyle: const TextStyle(color: Color(0xFFF5E6BE), fontSize: 12),
                            hintText: 'BMW, Toyota...',
                            hintStyle: const TextStyle(color: Color(0xFF64748B), fontSize: 12),
                            filled: true,
                            fillColor: const Color(0xFF121519),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: modelController,
                          style: const TextStyle(color: Colors.white, fontSize: 13),
                          decoration: InputDecoration(
                            labelText: 'Modelo *',
                            labelStyle: const TextStyle(color: Color(0xFFF5E6BE), fontSize: 12),
                            hintText: '320i, Civic...',
                            hintStyle: const TextStyle(color: Color(0xFF64748B), fontSize: 12),
                            filled: true,
                            fillColor: const Color(0xFF121519),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: TextField(
                          controller: colorController,
                          style: const TextStyle(color: Colors.white, fontSize: 13),
                          decoration: InputDecoration(
                            labelText: 'Cor',
                            labelStyle: const TextStyle(color: Color(0xFFF5E6BE), fontSize: 12),
                            hintText: 'Preto, Prata...',
                            hintStyle: const TextStyle(color: Color(0xFF64748B), fontSize: 12),
                            filled: true,
                            fillColor: const Color(0xFF121519),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text('Tipo de Veículo:', style: TextStyle(color: Color(0xFFF5E6BE), fontSize: 12, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF121519),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.3)),
                    ),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<String>(
                        isExpanded: true,
                        dropdownColor: const Color(0xFF1E232A),
                        value: vehicleType,
                        items: const [
                          DropdownMenuItem(value: 'sedan', child: Text('Sedan', style: TextStyle(color: Colors.white, fontSize: 13))),
                          DropdownMenuItem(value: 'suv', child: Text('SUV / Crossover', style: TextStyle(color: Colors.white, fontSize: 13))),
                          DropdownMenuItem(value: 'hatch', child: Text('Hatchback', style: TextStyle(color: Colors.white, fontSize: 13))),
                          DropdownMenuItem(value: 'pickup', child: Text('Picape / Caminhonete', style: TextStyle(color: Colors.white, fontSize: 13))),
                          DropdownMenuItem(value: 'moto', child: Text('Motocicleta', style: TextStyle(color: Colors.white, fontSize: 13))),
                          DropdownMenuItem(value: 'sports', child: Text('Esportivo / Supercar', style: TextStyle(color: Colors.white, fontSize: 13))),
                        ],
                        onChanged: (val) {
                          if (val != null) {
                            setModalState(() => vehicleType = val);
                          }
                        },
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFD4AF37),
                        foregroundColor: const Color(0xFF121519),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      onPressed: isSaving
                          ? null
                          : () async {
                              final plate = plateController.text.trim().toUpperCase();
                              final brand = brandController.text.trim();
                              final model = modelController.text.trim();
                              final color = colorController.text.trim();

                              if (plate.isEmpty || brand.isEmpty || model.isEmpty) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(content: Text('Preencha placa, marca e modelo do veículo!')),
                                );
                                return;
                              }

                              setModalState(() => isSaving = true);
                              final companyId = _selectedCompany?.id ?? 1;
                              final success = await ApiService.createVehicle(
                                companyId: companyId,
                                plate: plate,
                                brand: brand,
                                model: model,
                                color: color,
                                vehicleType: vehicleType,
                              );

                              if (context.mounted) {
                                Navigator.pop(context);
                                if (success) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(content: Text('Veículo $plate ($brand $model) cadastrado com sucesso!')),
                                  );
                                  final updatedVehicles = await ApiService.getMyVehicles();
                                  setState(() {
                                    _myVehicles = updatedVehicles;
                                  });
                                  onAdded?.call();
                                } else {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('Erro ao cadastrar veículo. Verifique a conexão.')),
                                  );
                                }
                              }
                            },
                      child: isSaving
                          ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF121519)))
                          : const Text('Salvar na Garagem', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
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

  // TAB: Sobre o Lava-Jato
  Widget _buildAboutTab(bool isTablet) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0xFF0F172A),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: const Color(0xFF1E293B)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                _selectedCompany?.name ?? '',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 6),
              Text(
                'Endereço: ${_selectedCompany?.address ?? ""}',
                style: const TextStyle(fontSize: 13, color: Color(0xFF94A3B8)),
              ),
              Text(
                'Telefone: ${_selectedCompany?.phone ?? ""}',
                style: const TextStyle(fontSize: 13, color: Color(0xFF94A3B8)),
              ),
              const Divider(color: Color(0xFF1E293B), height: 30),
              const Text(
                'Recursos Ativos no Plano do Lava-Jato:',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 10),
              _buildFeatureRow('Agendamento Mobile', _selectedCompany?.features.hasMobileBooking ?? false),
              _buildFeatureRow('Clube de Fidelidade', _selectedCompany?.features.hasLoyalty ?? false),
              _buildFeatureRow('Faturamento Mensal Frota', _selectedCompany?.features.hasMonthlyBilling ?? false),
              _buildFeatureRow('Vistoria Fotos Antes/Depois', _selectedCompany?.features.hasInspections ?? false),
              _buildFeatureRow('Comissões de Lavadores', _selectedCompany?.features.hasCommissions ?? false),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildFeatureRow(String name, bool enabled) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(
            enabled ? Icons.check_circle : Icons.cancel,
            color: enabled ? const Color(0xFF10B981) : const Color(0xFF64748B),
            size: 16,
          ),
          const SizedBox(width: 8),
          Text(
            name,
            style: TextStyle(
              fontSize: 12,
              color: enabled ? Colors.white : const Color(0xFF64748B),
            ),
          ),
        ],
      ),
    );
  }

  // Modal Adaptativo: BottomSheet em celular, Dialog centralizado em Tablet
  Future<void> _showAdaptiveModal({
    required BuildContext context,
    required Widget Function(BuildContext context) builder,
  }) async {
    final isTablet = MediaQuery.sizeOf(context).width >= 600;
    if (isTablet) {
      await showDialog(
        context: context,
        builder: (ctx) => Dialog(
          backgroundColor: const Color(0xFF0F172A),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(8),
              child: builder(ctx),
            ),
          ),
        ),
      );
    } else {
      await showModalBottomSheet(
        context: context,
        isScrollControlled: true,
        backgroundColor: const Color(0xFF0F172A),
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        builder: builder,
      );
    }
  }

  void _showLoginModal() {
    final emailController = TextEditingController(text: 'cliente@autoflow.com');
    final passwordController = TextEditingController(text: '123');
    bool isSubmitting = false;

    _showAdaptiveModal(
      context: context,
      builder: (modalContext) {
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
                        'Acessar Conta Motorista',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, color: Color(0xFF94A3B8)),
                        onPressed: () => Navigator.pop(context),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: emailController,
                    style: const TextStyle(color: Colors.white, fontSize: 14),
                    decoration: InputDecoration(
                      labelText: 'E-mail',
                      labelStyle: const TextStyle(color: Color(0xFF94A3B8)),
                      filled: true,
                      fillColor: const Color(0xFF1E293B),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                      prefixIcon: const Icon(Icons.email_outlined, color: Color(0xFF3B82F6), size: 20),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: passwordController,
                    obscureText: true,
                    style: const TextStyle(color: Colors.white, fontSize: 14),
                    decoration: InputDecoration(
                      labelText: 'Senha',
                      labelStyle: const TextStyle(color: Color(0xFF94A3B8)),
                      filled: true,
                      fillColor: const Color(0xFF1E293B),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                      prefixIcon: const Icon(Icons.lock_outline, color: Color(0xFF3B82F6), size: 20),
                    ),
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF2563EB),
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      onPressed: isSubmitting
                          ? null
                          : () async {
                              setModalState(() => isSubmitting = true);
                              final email = emailController.text.trim();
                              final pass = passwordController.text;
                              final success = await ApiService.login(email, pass);
                              if (context.mounted) {
                                Navigator.pop(context);
                                if (success) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('Login efetuado com sucesso!')),
                                  );
                                  setState(() {
                                    _isSelectingCompany = true;
                                  });
                                  _loadInitialData();
                                } else {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('Falha na autenticação. Verifique suas credenciais.')),
                                  );
                                }
                              }
                            },
                      child: isSubmitting
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                            )
                          : const Text('Entrar', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
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

  void _showLogoutConfirmDialog() {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          backgroundColor: const Color(0xFF0F172A),
          title: const Text('Sessão Conectada', style: TextStyle(color: Colors.white)),
          content: const Text('Deseja desconectar sua conta deste dispositivo?', style: TextStyle(color: Color(0xFF94A3B8))),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancelar', style: TextStyle(color: Color(0xFF94A3B8))),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFDC2626),
                foregroundColor: Colors.white,
              ),
              onPressed: () async {
                await ApiService.logout();
                if (context.mounted) {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Sessão encerrada com sucesso.')),
                  );
                  setState(() {
                    _isSelectingCompany = true;
                  });
                  _loadInitialData();
                }
              },
              child: const Text('Sair'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _showBookingDialog(ServiceItem service) async {
    if (!_isLoggedIn) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: const Color(0xFF1E232A),
          content: const Text('Faça login para agendar um serviço no seu veículo!', style: TextStyle(color: Colors.white)),
          action: SnackBarAction(
            label: 'Entrar VIP',
            textColor: const Color(0xFFD4AF37),
            onPressed: _showLoginModal,
          ),
        ),
      );
      return;
    }

    final vehicles = await ApiService.getMyVehicles();
    if (!mounted) return;

    if (vehicles.isEmpty) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          backgroundColor: const Color(0xFF1E232A),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20), side: BorderSide(color: const Color(0xFFA3734C).withValues(alpha: 0.35))),
          title: const Row(
            children: [
              Icon(Icons.directions_car, color: Color(0xFFD4AF37)),
              SizedBox(width: 8),
              Text('Cadastrar Veículo', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
            ],
          ),
          content: const Text(
            'Você ainda não possui veículos cadastrados na sua Garagem. Deseja cadastrar seu carro agora para agendar?',
            style: TextStyle(color: Color(0xFF9A9FA8), fontSize: 13),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancelar', style: TextStyle(color: Color(0xFF9A9FA8))),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFD4AF37),
                foregroundColor: const Color(0xFF121519),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              onPressed: () {
                Navigator.pop(ctx);
                _showAddVehicleDialog(onAdded: () => _showBookingDialog(service));
              },
              child: const Text('Cadastrar Carro', style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      );
      return;
    }

    VehicleItem selectedVehicle = vehicles.first;
    String scheduledDate = DateTime.now().add(const Duration(days: 1)).toIso8601String().split('T')[0];
    String scheduledTime = '10:00';
    final notesController = TextEditingController();
    bool isSubmitting = false;

    _showAdaptiveModal(
      context: context,
      builder: (modalContext) {
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
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('NOVO AGENDAMENTO', style: TextStyle(fontSize: 10, color: Color(0xFF1EA8D7), fontWeight: FontWeight.bold, letterSpacing: 0.5)),
                            Text(
                              service.name,
                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, color: Color(0xFF9A9FA8)),
                        onPressed: () => Navigator.pop(context),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Escolha o seu Veículo:', style: TextStyle(color: Color(0xFFF5E6BE), fontSize: 12, fontWeight: FontWeight.bold)),
                      InkWell(
                        onTap: () {
                          Navigator.pop(context);
                          _showAddVehicleDialog(onAdded: () => _showBookingDialog(service));
                        },
                        child: const Text('+ Novo Carro', style: TextStyle(color: Color(0xFF1EA8D7), fontSize: 11, fontWeight: FontWeight.bold)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF121519),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.35)),
                    ),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<VehicleItem>(
                        isExpanded: true,
                        dropdownColor: const Color(0xFF1E232A),
                        value: selectedVehicle,
                        items: vehicles.map((v) {
                          return DropdownMenuItem(
                            value: v,
                            child: Text('${v.plate} - ${v.brand} ${v.model} (${v.color})', style: const TextStyle(color: Colors.white, fontSize: 13)),
                          );
                        }).toList(),
                        onChanged: (val) {
                          if (val != null) {
                            setModalState(() => selectedVehicle = val);
                          }
                        },
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Data:', style: TextStyle(color: Color(0xFFF5E6BE), fontSize: 12, fontWeight: FontWeight.bold)),
                            const SizedBox(height: 6),
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: const Color(0xFF121519),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.35)),
                              ),
                              child: Text(scheduledDate, style: const TextStyle(color: Colors.white, fontSize: 13)),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Horário:', style: TextStyle(color: Color(0xFFF5E6BE), fontSize: 12, fontWeight: FontWeight.bold)),
                            const SizedBox(height: 6),
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: const Color(0xFF121519),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: const Color(0xFFA3734C).withValues(alpha: 0.35)),
                              ),
                              child: Text(scheduledTime, style: const TextStyle(color: Colors.white, fontSize: 13)),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  TextField(
                    controller: notesController,
                    style: const TextStyle(color: Colors.white, fontSize: 13),
                    decoration: InputDecoration(
                      labelText: 'Observações (opcional)',
                      labelStyle: const TextStyle(color: Color(0xFF9A9FA8), fontSize: 12),
                      filled: true,
                      fillColor: const Color(0xFF121519),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                    ),
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFD4AF37),
                        foregroundColor: const Color(0xFF121519),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      onPressed: isSubmitting
                          ? null
                          : () async {
                              if (_selectedCompany == null) return;
                              setModalState(() => isSubmitting = true);
                              final ok = await ApiService.bookAppointment(
                                companyId: _selectedCompany!.id,
                                vehicleId: selectedVehicle.id,
                                serviceTypeId: service.id,
                                date: scheduledDate,
                                time: scheduledTime,
                                notes: notesController.text.trim(),
                              );
                              if (context.mounted) {
                                Navigator.pop(context);
                                if (ok) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(content: Text('Agendamento confirmado para ${selectedVehicle.plate}!')),
                                  );
                                } else {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('Não foi possível confirmar o agendamento.')),
                                  );
                                }
                              }
                            },
                      child: isSubmitting
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                            )
                          : const Text('Confirmar Agendamento', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
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
}
