import 'package:flutter/material.dart';
import 'package:mapbox_maps_flutter/mapbox_maps_flutter.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/network/websocket_service.dart';
import '../../../../core/network/emergencia_service.dart';

class TrackingScreen extends StatefulWidget {
  final int nroEmergencia;
  final String ubicacionCliente;
  final int idCliente;

  const TrackingScreen({
    super.key,
    required this.nroEmergencia,
    required this.ubicacionCliente,
    required this.idCliente,
  });

  @override
  State<TrackingScreen> createState() => _TrackingScreenState();
}

class _TrackingScreenState extends State<TrackingScreen> {
  MapboxMap? mapboxMap;
  CircleAnnotationManager? circleAnnotationManager;
  PointAnnotationManager? pointAnnotationManager;
  final WebSocketService _wsService = WebSocketService();
  final EmergenciaService _emergenciaService = EmergenciaService();
  
  Point? _personnelPoint;
  late Point _clientPoint;
  String _eta = "En espera...";

  @override
  void initState() {
    super.initState();
    MapboxOptions.setAccessToken(dotenv.env['MAPBOX_ACCESS_TOKEN'] ?? "");
    
    final coords = widget.ubicacionCliente.split(',');
    _clientPoint = Point(
      coordinates: Position(
        double.parse(coords[1].trim()), // Longitude
        double.parse(coords[0].trim()), // Latitude
      ),
    );

    _initWebSocket();
    _loadInitialTrackingInfo();
  }

  @override
  void dispose() {
    _wsService.disconnect();
    super.dispose();
  }

  void _initWebSocket() {
    _wsService.connectCliente(widget.idCliente, (payload) {
      if (mounted && payload['type'] == 'LOCATION_UPDATE') {
        final data = payload['data'];
        if (data['nro'] == widget.nroEmergencia) {
          setState(() {
            _personnelPoint = Point(
              coordinates: Position(data['longitud'], data['latitud']),
            );
            _eta = data['eta'] ?? _eta;
          });
          _updateMarkers();
        }
      }
    });
  }

  Future<void> _loadInitialTrackingInfo() async {
    try {
      final data = await _emergenciaService.getTrackingInfo(widget.nroEmergencia);
      if (data['ubicacion_personal_real'] != null) {
        final parts = data['ubicacion_personal_real'].split(',');
        setState(() {
          _personnelPoint = Point(
            coordinates: Position(
              double.parse(parts[1].trim()),
              double.parse(parts[0].trim()),
            ),
          );
          _eta = data['tiempo_llegada_estimado'] ?? _eta;
        });
        _updateMarkers();
      }
    } catch (e) {
      debugPrint("Error cargando info inicial de tracking: $e");
    }
  }

  void _onMapCreated(MapboxMap mapboxMap) {
    this.mapboxMap = mapboxMap;
    
    // Crear gestores de anotaciones
    mapboxMap.annotations.createCircleAnnotationManager().then((value) {
      circleAnnotationManager = value;
      _updateMarkers();
    });
    mapboxMap.annotations.createPointAnnotationManager().then((value) {
      pointAnnotationManager = value;
      _updateMarkers();
    });
  }

  Future<void> _updateMarkers() async {
    if (circleAnnotationManager == null || pointAnnotationManager == null) return;
    
    await circleAnnotationManager!.deleteAll();
    await pointAnnotationManager!.deleteAll();

    // --- MARCADOR CLIENTE ---
    // Círculo
    await circleAnnotationManager!.create(
      CircleAnnotationOptions(
        geometry: _clientPoint,
        circleColor: Colors.red.value,
        circleRadius: 10.0,
        circleStrokeWidth: 2.0,
        circleStrokeColor: Colors.white.value,
      ),
    );
    // Texto
    await pointAnnotationManager!.create(
      PointAnnotationOptions(
        geometry: _clientPoint,
        textField: "MI UBICACIÓN",
        textOffset: [0, -2],
        textSize: 10.0,
        textColor: Colors.red.value,
      ),
    );

    // --- MARCADOR PERSONAL ---
    if (_personnelPoint != null) {
      // Círculo
      await circleAnnotationManager!.create(
        CircleAnnotationOptions(
          geometry: _personnelPoint!,
          circleColor: Colors.blue.value,
          circleRadius: 10.0,
          circleStrokeWidth: 2.0,
          circleStrokeColor: Colors.white.value,
        ),
      );
      // Texto
      await pointAnnotationManager!.create(
        PointAnnotationOptions(
          geometry: _personnelPoint!,
          textField: "MECÁNICO",
          textOffset: [0, -2],
          textSize: 10.0,
          textColor: Colors.blue.value,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Seguimiento en Vivo'),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
      ),
      body: Stack(
        children: [
          MapWidget(
            key: const ValueKey("trackingMap"),
            onMapCreated: _onMapCreated,
            cameraOptions: CameraOptions(
              center: _clientPoint,
              zoom: 13.0,
            ),
          ),
          
          // Recenter Button
          Positioned(
            right: 16,
            top: 100,
            child: FloatingActionButton.small(
              onPressed: () {
                if (_personnelPoint != null) {
                  mapboxMap?.setCamera(CameraOptions(
                    center: _personnelPoint!,
                    zoom: 15.0,
                  ));
                } else {
                  mapboxMap?.setCamera(CameraOptions(
                    center: _clientPoint,
                    zoom: 15.0,
                  ));
                }
              },
              backgroundColor: Colors.white,
              child: const Icon(Icons.my_location, color: AppColors.primary),
            ),
          ),
          
          // Info Panel
          Positioned(
            bottom: 24, left: 16, right: 16,
            child: Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                  color: Colors.black.withValues(alpha: 0.1),
                  blurRadius: 20,
                  offset: const Offset(0, 10),
                  ),
                  ],
                  ),
                  child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                  Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(Icons.timer, color: AppColors.primary),
                    ),

                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Tiempo estimado de llegada',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Text(
                              _eta,
                              style: const TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: Colors.black,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  const LinearProgressIndicator(
                    valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
                    backgroundColor: AppColors.surfaceContainerHigh,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'El mecánico se está desplazando hacia tu ubicación',
                    style: TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
