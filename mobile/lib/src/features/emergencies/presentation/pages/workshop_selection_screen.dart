import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:mapbox_maps_flutter/mapbox_maps_flutter.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class WorkshopSelectionScreen extends StatefulWidget {
  final String diagnostico;
  final String prioridad;
  final String especialidad;
  final List<dynamic> talleres;
  final String ubicacionCliente;

  const WorkshopSelectionScreen({
    super.key,
    required this.diagnostico,
    required this.prioridad,
    required this.especialidad,
    required this.talleres,
    required this.ubicacionCliente,
  });

  @override
  State<WorkshopSelectionScreen> createState() => _WorkshopSelectionScreenState();
}

class _WorkshopSelectionScreenState extends State<WorkshopSelectionScreen> {
  MapboxMap? mapboxMap;
  CircleAnnotationManager? circleAnnotationManager;
  PointAnnotationManager? pointAnnotationManager;
  int? _selectedWorkshopId;
  late Point _clientPoint;

  // NUEVO: Estado para búsqueda dinámica
  double _radioKm = 2.0;
  List<dynamic> _currentTalleres = [];
  bool _isSearching = false;
  final String _baseUrl = dotenv.env['API_URL'] ?? 'http://192.168.1.15:8000';

  @override
  void initState() {
    super.initState();
    _currentTalleres = List.from(widget.talleres);
    // Configuración global del token
    MapboxOptions.setAccessToken(dotenv.env['MAPBOX_ACCESS_TOKEN'] ?? "");
    
    final coords = widget.ubicacionCliente.split(',');
    _clientPoint = Point(
      coordinates: Position(
        double.parse(coords[1].trim()), // Longitude
        double.parse(coords[0].trim()), // Latitude
      ),
    );
  }

  void _onMapCreated(MapboxMap mapboxMap) {
    this.mapboxMap = mapboxMap;
    
    mapboxMap.annotations.createCircleAnnotationManager().then((value) {
      circleAnnotationManager = value;
      _addMarkers();
    });
    mapboxMap.annotations.createPointAnnotationManager().then((value) {
      pointAnnotationManager = value;
      _addMarkers();
    });
  }

  Future<void> _addMarkers() async {
    if (circleAnnotationManager == null || pointAnnotationManager == null) return;
    
    // Limpiar marcadores previos
    await circleAnnotationManager!.deleteAll();
    await pointAnnotationManager!.deleteAll();

    // --- MARCADOR CLIENTE ---
    await circleAnnotationManager!.create(
      CircleAnnotationOptions(
        geometry: _clientPoint,
        circleColor: Colors.redAccent.value,
        circleRadius: 8.0,
        circleStrokeWidth: 2.0,
        circleStrokeColor: Colors.white.value,
      ),
    );
    await pointAnnotationManager!.create(
      PointAnnotationOptions(
        geometry: _clientPoint,
        textField: "TÚ",
        textOffset: [0, -2],
        textSize: 10.0,
        textColor: Colors.redAccent.value,
      ),
    );

    // --- MARCADORES TALLERES ---
    for (var taller in _currentTalleres) {
      final lat = taller['latitud']?.toDouble() ?? (_clientPoint.coordinates.lat + 0.002);
      final lng = taller['longitud']?.toDouble() ?? (_clientPoint.coordinates.lng + 0.002);
      final point = Point(coordinates: Position(lng, lat));

      await circleAnnotationManager!.create(
        CircleAnnotationOptions(
          geometry: point,
          circleColor: Colors.indigoAccent.value,
          circleRadius: 7.0,
          circleStrokeWidth: 2.0,
          circleStrokeColor: Colors.white.value,
        ),
      );

      await pointAnnotationManager!.create(
        PointAnnotationOptions(
          geometry: point,
          textField: taller['nombre_taller'],
          textOffset: [0, -2],
          textSize: 9.0,
          textColor: Colors.indigoAccent.value,
        ),
      );
    }
  }

  // NUEVO: Método para buscar talleres con nuevo radio
  Future<void> _buscarConNuevoRadio(double radio) async {
    setState(() {
      _radioKm = radio;
      _isSearching = true;
      _selectedWorkshopId = null;
    });

    try {
      const storage = FlutterSecureStorage();
      String? token = await storage.read(key: 'jwt_token');
      final url = Uri.parse('$_baseUrl/emergencias/buscar-talleres');

      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          if (token != null) 'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          "ubicacion_cliente": widget.ubicacionCliente,
          "especialidad": widget.especialidad,
          "radio_km": radio
        }),
      );

      if (response.statusCode == 200) {
        final List<dynamic> nuevosTalleres = jsonDecode(response.body);
        setState(() {
          _currentTalleres = nuevosTalleres;
        });
        _addMarkers();
      }
    } catch (e) {
      debugPrint("Error buscando talleres: $e");
    } finally {
      setState(() => _isSearching = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final selectedWorkshop = _selectedWorkshopId == null 
        ? null 
        : _currentTalleres.firstWhere((t) => t['id'] == _selectedWorkshopId, orElse: () => null);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Selecciona un Taller', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
      ),
      body: Stack(
        children: [
          MapWidget(
            key: const ValueKey("mapWidget"),
            onMapCreated: _onMapCreated,
            cameraOptions: CameraOptions(
              center: _clientPoint,
              zoom: 13.0,
            ),
          ),
          
          // Panel de Información Superior
          Positioned(
            top: 16, left: 16, right: 16,
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.95),
                    borderRadius: BorderRadius.circular(12),
                    boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 10)],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.psychology, color: Colors.purple),
                          const SizedBox(width: 8),
                          Text('Análisis Gemini: ${widget.especialidad}', style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.purple)),
                          const Spacer(),
                          _buildPriorityBadge(widget.prioridad),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(widget.diagnostico, style: const TextStyle(fontSize: 13, color: Colors.black87), maxLines: 2, overflow: TextOverflow.ellipsis),
                    ],
                  ),
                ),
                const SizedBox(height: 8),
                // NUEVO: Selector de Radio
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(30),
                    boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 5)],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.radar, size: 18, color: Colors.red),
                      const SizedBox(width: 8),
                      const Text('Radio:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                      const SizedBox(width: 4),
                      _buildRadioOption(2.0),
                      _buildRadioOption(7.0),
                      _buildRadioOption(10.0),
                    ],
                  ),
                ),
              ],
            ),
          ),

          if (_isSearching)
            const Center(child: CircularProgressIndicator(color: Colors.red)),

          if (_selectedWorkshopId == null && !_isSearching)
            Positioned(
              bottom: 20, left: 0, right: 0,
              child: _currentTalleres.isEmpty 
                ? Center(
                    child: Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
                      child: const Text('No hay talleres con esta especialidad en este radio.', style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
                    ),
                  )
                : SizedBox(
                height: 120,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: _currentTalleres.length,
                  itemBuilder: (context, index) {
                    final taller = _currentTalleres[index];
                    return GestureDetector(
                      onTap: () {
                        setState(() => _selectedWorkshopId = taller['id']);
                        mapboxMap?.setCamera(CameraOptions(
                          center: Point(coordinates: Position(
                            taller['longitud']?.toDouble() ?? _clientPoint.coordinates.lng,
                            taller['latitud']?.toDouble() ?? _clientPoint.coordinates.lat,
                          )),
                          zoom: 15.0,
                        ));
                      },
                      child: Container(
                        width: 250, margin: const EdgeInsets.only(right: 12),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16), boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 8)]),
                        child: Row(
                          children: [
                            Container(
                              width: 60, height: 60,
                              decoration: BoxDecoration(borderRadius: BorderRadius.circular(10), image: DecorationImage(image: NetworkImage(taller['foto_perfil'] ?? 'https://via.placeholder.com/150'), fit: BoxFit.cover)),
                            ),
                            const SizedBox(width: 12),
                            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [
                              Text(taller['nombre_taller'], style: const TextStyle(fontWeight: FontWeight.bold)),
                              Text('${taller['distancia_km']} km', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                              Text(taller['especialidades'].join(", "), style: const TextStyle(color: Colors.red, fontSize: 10), maxLines: 1),
                            ])),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
            ),

          if (selectedWorkshop != null)
            Positioned(
              bottom: 20, left: 16, right: 16,
              child: Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20), boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 20)]),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.check_circle, color: Colors.green),
                        const SizedBox(width: 10),
                        Expanded(child: Text('Seleccionado: ${selectedWorkshop['nombre_taller']}', style: const TextStyle(fontWeight: FontWeight.bold))),
                        IconButton(icon: const Icon(Icons.close), onPressed: () => setState(() => _selectedWorkshopId = null)),
                      ],
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: () => Navigator.pop(context, selectedWorkshop['id']),
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.red.shade700, padding: const EdgeInsets.symmetric(vertical: 14), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
                        child: const Text('SOLICITAR AYUDA AQUÍ', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildRadioOption(double radio) {
    bool isSelected = _radioKm == radio;
    return GestureDetector(
      onTap: () => _buscarConNuevoRadio(radio),
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 4),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: isSelected ? Colors.red : Colors.grey.shade200,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          '${radio.toInt()}km',
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.black,
            fontSize: 11,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ),
    );
  }

  Widget _buildPriorityBadge(String priority) {
    Color color = Colors.green;
    if (priority == 'alta') color = Colors.red;
    if (priority == 'media') color = Colors.orange;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(8)),
      child: Text(priority.toUpperCase(), style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold)),
    );
  }
}
