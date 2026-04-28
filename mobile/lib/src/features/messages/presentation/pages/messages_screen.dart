import 'dart:ui';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../../../core/theme/app_colors.dart';
import 'chat_page.dart';

class MessagesScreen extends StatefulWidget {
  const MessagesScreen({super.key});

  @override
  State<MessagesScreen> createState() => _MessagesScreenState();
}

class _MessagesScreenState extends State<MessagesScreen> {
  List<dynamic> _emergencias = [];
  bool _isLoading = true;
  final String _baseUrl = dotenv.env['API_URL'] ?? 'http://10.0.2.2:8000';

  @override
  void initState() {
    super.initState();
    _cargarEmergencias();
  }

  Future<void> _cargarEmergencias() async {
    try {
      const storage = FlutterSecureStorage();
      String? token = await storage.read(key: 'jwt_token');
      final url = Uri.parse('$_baseUrl/emergencias/cliente/mis-emergencias');

      final response = await http.get(
        url,
        headers: {
          'Accept': 'application/json',
          if (token != null) 'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            _emergencias = jsonDecode(response.body);
            _isLoading = false;
          });
        }
      }
    } catch (e) {
      print("Error cargando emergencias: $e");
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      extendBodyBehindAppBar: true,
      extendBody: true,
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(kToolbarHeight),
        child: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
            child: AppBar(
              backgroundColor: AppColors.surface.withOpacity(0.7),
              elevation: 0,
              title: const Text(
                'Emergencia Vehicular',
                style: TextStyle(
                  fontFamily: 'Manrope',
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                  color: Colors.black87,
                ),
              ),
            ),
          ),
        ),
      ),
      body: SafeArea(
        top: false,
        child: _isLoading 
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _cargarEmergencias,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: EdgeInsets.only(
                  top: MediaQuery.of(context).padding.top + kToolbarHeight + 16,
                  left: 16,
                  right: 16,
                  bottom: 120,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Mis Mensajes',
                      style: TextStyle(
                        fontFamily: 'Manrope',
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        color: AppColors.onSurface,
                      ),
                    ),
                    const SizedBox(height: 24),

                    if (_emergencias.isEmpty)
                      const Center(
                        child: Padding(
                          padding: EdgeInsets.all(32.0),
                          child: Text('No tienes emergencias activas para chatear.'),
                        ),
                      )
                    else
                      ListView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: _emergencias.length,
                        itemBuilder: (context, index) {
                          final e = _emergencias[index];
                          // Solo permitimos chat si la emergencia ha sido aceptada por un taller
                          final bool tieneTaller = e['id_personal'] != null;

                          return _buildChatItem(
                            nro: e['nro'],
                            name: tieneTaller ? 'Taller Asignado' : 'Esperando Taller...',
                            message: e['descripcion'],
                            status: e['estado'],
                            isClickable: tieneTaller,
                          );
                        },
                      ),
                  ],
                ),
              ),
            ),
      ),
      bottomNavigationBar: _buildBottomNav(context),
    );
  }

  Widget _buildChatItem({
    required int nro,
    required String name,
    required String message,
    required String status,
    required bool isClickable,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.all(12),
        leading: CircleAvatar(
          backgroundColor: isClickable ? Colors.red.shade100 : Colors.grey.shade200,
          child: Icon(
            isClickable ? Icons.chat : Icons.hourglass_empty,
            color: isClickable ? Colors.red : Colors.grey,
          ),
        ),
        title: Text(
          name,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(message, maxLines: 1, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: _getStatusColor(status).withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                status.toUpperCase(),
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: _getStatusColor(status),
                ),
              ),
            ),
          ],
        ),
        trailing: isClickable 
          ? const Icon(Icons.arrow_forward_ios, size: 16) 
          : null,
        onTap: isClickable 
          ? () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => ChatPage(
                  nroEmergencia: nro,
                  nombreReceptor: name,
                ),
              ),
            )
          : null,
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'espera': return Colors.orange;
      case 'atendiendo': return Colors.blue;
      case 'terminado': return Colors.green;
      default: return Colors.grey;
    }
  }

  Widget _buildBottomNav(BuildContext context) {
    return ClipRRect(
      borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
        child: Container(
          color: Colors.white.withOpacity(0.8),
          child: BottomNavigationBar(
            currentIndex: 2,
            type: BottomNavigationBarType.fixed,
            selectedItemColor: const Color(0xFFB91C1C),
            onTap: (index) {
              if (index == 0) Navigator.pushReplacementNamed(context, '/home');
              if (index == 1) Navigator.pushReplacementNamed(context, '/workshops');
            },
            items: const [
              BottomNavigationBarItem(icon: Icon(Icons.emergency_share), label: 'Emergency'),
              BottomNavigationBarItem(icon: Icon(Icons.car_repair), label: 'Workshops'),
              BottomNavigationBarItem(icon: Icon(Icons.chat_bubble), label: 'Messages'),
              BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
            ],
          ),
        ),
      ),
    );
  }
}
