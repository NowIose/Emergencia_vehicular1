import 'dart:async';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/network/emergencia_service.dart';

class PersonnelTrackingPage extends StatefulWidget {
  const PersonnelTrackingPage({super.key});

  @override
  State<PersonnelTrackingPage> createState() => _PersonnelTrackingPageState();
}

class _PersonnelTrackingPageState extends State<PersonnelTrackingPage> {
  final EmergenciaService _emergenciaService = EmergenciaService();
  List<dynamic> _atenciones = [];
  bool _isLoading = true;
  int? _trackingEmergenciaNro;
  StreamSubscription<Position>? _positionStream;

  @override
  void initState() {
    super.initState();
    _loadAtenciones();
  }

  @override
  void dispose() {
    _positionStream?.cancel();
    super.dispose();
  }

  Future<void> _loadAtenciones() async {
    try {
      setState(() => _isLoading = true);
      final data = await _emergenciaService.getAtencionesPersonal();
      setState(() {
        _atenciones = data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al cargar atenciones: $e')),
        );
      }
    }
  }

  Future<void> _toggleTracking(int nro) async {
    if (_trackingEmergenciaNro == nro) {
      // Detener tracking
      await _positionStream?.cancel();
      setState(() {
        _trackingEmergenciaNro = null;
        _positionStream = null;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Ubicación detenida')),
        );
      }
    } else {
      // Iniciar tracking
      bool serviceEnabled;
      LocationPermission permission;

      serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Servicio de ubicación desactivado')),
          );
        }
        return;
      }

      permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) return;
      }

      setState(() {
        _trackingEmergenciaNro = nro;
      });

      _positionStream = Geolocator.getPositionStream(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          distanceFilter: 10, // Actualizar cada 10 metros
        ),
      ).listen((Position position) {
        _emergenciaService.updateUbicacion(
          nro,
          position.latitude,
          position.longitude,
        ).catchError((e) {
          debugPrint("Error enviando ubicación: $e");
        });
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Compartiendo ubicación en tiempo real')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Mis Atenciones',
          style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
        ),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 1,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _atenciones.isEmpty
              ? const Center(child: Text('No tienes emergencias asignadas actualmente.'))
              : RefreshIndicator(
                  onRefresh: _loadAtenciones,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _atenciones.length,
                    itemBuilder: (context, index) {
                      final emer = _atenciones[index];
                      final isTracking = _trackingEmergenciaNro == emer['nro'];

                      return Card(
                        margin: const EdgeInsets.only(bottom: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                        elevation: 3,
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    'Emergencia #${emer['nro']}',
                                    style: const TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 18,
                                    ),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 8,
                                      vertical: 4,
                                    ),
                                    decoration: BoxDecoration(
                                      color: AppColors.primary.withValues(alpha: 0.1),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Text(
                                      emer['estado'].toString().toUpperCase(),
                                      style: const TextStyle(
                                        color: AppColors.primary,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 12,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 12),
                              Text(
                                emer['descripcion'] ?? 'Sin descripción',
                                style: const TextStyle(color: Colors.black87),
                              ),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  const Icon(Icons.location_on, size: 16, color: Colors.grey),
                                  const SizedBox(width: 4),
                                  Expanded(
                                    child: Text(
                                      emer['ubicacion_real'] ?? 'Desconocida',
                                      style: const TextStyle(color: Colors.grey, fontSize: 13),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 20),
                              SizedBox(
                                width: double.infinity,
                                child: ElevatedButton.icon(
                                  onPressed: () => _toggleTracking(emer['nro']),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: isTracking ? Colors.red : Colors.green,
                                    foregroundColor: Colors.white,
                                    padding: const EdgeInsets.symmetric(vertical: 12),
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                  ),
                                  icon: Icon(isTracking ? Icons.stop : Icons.navigation),
                                  label: Text(
                                    isTracking ? 'DETENER SEGUIMIENTO' : 'INICIAR SEGUIMIENTO',
                                    style: const TextStyle(fontWeight: FontWeight.bold),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
