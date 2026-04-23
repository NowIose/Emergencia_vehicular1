import 'dart:io';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

final String _baseUrl = dotenv.env['API_URL'] ?? 'http://192.168.1.15:8000';

class EmergencyBubble extends StatefulWidget {
  final int? idCliente;
  final int? idVehiculoSeleccionado;

  const EmergencyBubble({
    super.key,
    this.idCliente,
    this.idVehiculoSeleccionado,
  });

  @override
  State<EmergencyBubble> createState() => _EmergencyBubbleState();
}

class _EmergencyBubbleState extends State<EmergencyBubble> {
  double _xOffset = 20;
  double _yOffset = 150;

  // 1. Controladores y estado
  final TextEditingController _descripcionController = TextEditingController();
  String? _ubicacionActual;
  bool _isLoading = false;

  // Lista de vehículos y el seleccionado
  List<dynamic> _misVehiculos = [];
  int? _vehiculoSeleccionado;

  // Fotos
  final ImagePicker _picker = ImagePicker();
  List<File> _fotosTomadas = [];
  bool _isUploadingFotos = false;

  @override
  void initState() {
    super.initState();
    _vehiculoSeleccionado = widget.idVehiculoSeleccionado;
  }

  // 1. Obtener vehículos del usuario
  Future<void> _cargarMisVehiculos(StateSetter setModalState) async {
    try {
      const storage = FlutterSecureStorage();
      String? token = await storage.read(key: 'jwt_token');
      final url = Uri.parse('$_baseUrl/vehiculos/mis-vehiculos');

      final response = await http.get(
        url,
        headers: {
          'Accept': 'application/json',
          if (token != null) 'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        setModalState(() {
          _misVehiculos = jsonDecode(response.body);
          if (_misVehiculos.isNotEmpty && _vehiculoSeleccionado == null) {
            _vehiculoSeleccionado = _misVehiculos.first['id'];
          }
        });
      }
    } catch (e) {
      debugPrint("Error cargando vehículos: $e");
    }
  }

  // 2. Tomar foto
  Future<void> _tomarFoto(StateSetter setModalState) async {
    if (_fotosTomadas.length >= 3) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Máximo 3 fotos permitidas')),
      );
      return;
    }
    final XFile? photo = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 70,
    );
    if (photo != null) {
      setModalState(() {
        _fotosTomadas.add(File(photo.path));
      });
    }
  }

  // 3. Subir fotos al backend (que las manda a Cloudinary)
  Future<List<String>> _subirFotos() async {
    List<String> urls = [];
    final urlUpload = Uri.parse('$_baseUrl/usuarios/upload-image');

    for (File foto in _fotosTomadas) {
      var request = http.MultipartRequest('POST', urlUpload);
      request.files.add(await http.MultipartFile.fromPath('file', foto.path));
      request.fields['folder'] = 'emergencia_vehicular/emergencias';

      var response = await request.send();
      if (response.statusCode == 201 || response.statusCode == 200) {
        var respStr = await response.stream.bytesToString();
        var jsonResp = jsonDecode(respStr);
        urls.add(jsonResp['url']);
      }
    }
    return urls;
  }

  // 4. Función para obtener GPS
  Future<void> _obtenerUbicacion() async {
    bool serviceEnabled;
    LocationPermission permission;

    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Por favor habilita el GPS')),
      );
      return;
    }

    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        return;
      }
    }

    Position position = await Geolocator.getCurrentPosition();
    setState(() {
      // Guardamos la ubicación en formato "Latitud, Longitud"
      _ubicacionActual = '${position.latitude}, ${position.longitude}';
    });

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('📍 Ubicación capturada con éxito')),
    );
  }

  // 3. Función para enviar al Backend
  Future<void> _enviarEmergencia(BuildContext context) async {
    if (_descripcionController.text.isEmpty || _ubicacionActual == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Añade una descripción y tu ubicación')),
      );
      return;
    }
    if (_vehiculoSeleccionado == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Por favor selecciona un vehículo')),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      // Primero subir las fotos
      List<String> fotosUrls = [];
      if (_fotosTomadas.isNotEmpty) {
        setState(() => _isUploadingFotos = true);
        fotosUrls = await _subirFotos();
        setState(() => _isUploadingFotos = false);
      }
      const storage = FlutterSecureStorage();
      String? token = await storage.read(key: 'jwt_token');

      // Cambia esta IP por la de tu servidor backend local (ej. 10.0.2.2 para emulador Android o tu IP local para Windows/Dispositivo físico)
      final url = Uri.parse('$_baseUrl/emergencias/');
      print("Enviando a: $url"); // Debug para ver la ruta
      print("Token: ${token != null ? 'Presente' : 'Nulo'}");
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          if (token != null) 'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          "id_vehiculo": _vehiculoSeleccionado,
          "ubicacion_real": _ubicacionActual,
          "descripcion": _descripcionController.text,
          "prioridad": "alta",
          "fotos": fotosUrls,
        }),
      );
      print("Status Code: ${response.statusCode}");
      print("Response Body: ${response.body}");
      if (response.statusCode >= 200 && response.statusCode < 300) {
        // Éxito
        if (mounted) Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('🚨 Alerta enviada exitosamente')),
        );
        _descripcionController.clear();
        _ubicacionActual = null;
        _fotosTomadas.clear();
      } else {
        // Error controlado por el Backend (401, 403, 422)
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error ${response.statusCode}: ${response.body}'),
          ),
        );
      }
    } catch (e) {
      // Error de red (IP incorrecta o servidor apagado)
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Error de conexión: $e')));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showEmergencySheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) {
        // Usamos StatefulBuilder para poder actualizar la UI dentro del Modal (ej. mostrar un loader)
        // Cargar vehículos al abrir el modal

        return StatefulBuilder(
          builder: (BuildContext context, StateSetter setModalState) {
            // 1. CARGA INICIAL: Solo si la lista de vehículos está vacía
            if (_misVehiculos.isEmpty) {
              _cargarMisVehiculos(setModalState);
            }

            return Padding(
              padding: EdgeInsets.only(
                bottom: MediaQuery.of(context).viewInsets.bottom,
                left: 24,
                right: 24,
                top: 24,
              ),
              child: SingleChildScrollView(
                // Añadido ScrollView para evitar overflow con el teclado
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Título
                    const Text(
                      'Solicitar Auxilio',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.red,
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Selector de Vehículo
                    if (_misVehiculos.isNotEmpty)
                      DropdownButtonFormField<int>(
                        decoration: InputDecoration(
                          filled: true,
                          fillColor: Colors.grey.shade100,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: BorderSide.none,
                          ),
                          hintText: 'Selecciona tu vehículo',
                        ),
                        value:
                            _misVehiculos.any(
                              (v) => v['id'] == _vehiculoSeleccionado,
                            )
                            ? _vehiculoSeleccionado
                            : null,
                        items: _misVehiculos.map((v) {
                          return DropdownMenuItem<int>(
                            // Asegúrate de que v['id'] sea realmente un int.
                            // Si viene como String, cámbialo a: int.tryParse(v['id'].toString())
                            value: v['id'] is int
                                ? v['id']
                                : int.tryParse(v['id'].toString()),
                            child: Text(
                              '${v['marca']} ${v['modelo']} - ${v['placa']}',
                            ),
                          );
                        }).toList(),
                        onChanged: (val) {
                          setModalState(() {
                            _vehiculoSeleccionado = val;
                          });
                        },
                      )
                    else
                      const Center(
                        child: Padding(
                          padding: EdgeInsets.all(8.0),
                          child: CircularProgressIndicator(),
                        ),
                      ),

                    const SizedBox(height: 16),

                    TextField(
                      controller:
                          _descripcionController, // Añadido el controlador
                      maxLines: 3,
                      decoration: InputDecoration(
                        hintText: '¿Qué le ocurrió a tu vehículo?',
                        filled: true,
                        fillColor: Colors
                            .grey
                            .shade200, // Ajuste de color para que se vea el texto
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    Row(
                      children: [
                        // Botón de cámara
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: () => _tomarFoto(setModalState),
                            icon: const Icon(Icons.camera_alt),
                            label: Text('Foto (${_fotosTomadas.length}/3)'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: () async {
                              await _obtenerUbicacion();
                              // Refresca el modal si necesitas cambiar el color del botón al tener GPS
                              setModalState(() {});
                            },
                            icon: Icon(
                              _ubicacionActual != null
                                  ? Icons.check_circle
                                  : Icons.location_on,
                              size: 20,
                              color: _ubicacionActual != null
                                  ? Colors.green
                                  : null,
                            ),
                            label: Text(
                              _ubicacionActual != null
                                  ? 'GPS Listo'
                                  : 'Ubicación',
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),

                    // Vista previa de fotos
                    if (_fotosTomadas.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 8.0),
                        child: SizedBox(
                          height: 80,
                          child: ListView.builder(
                            scrollDirection: Axis.horizontal,
                            itemCount: _fotosTomadas.length,
                            itemBuilder: (context, index) {
                              return Stack(
                                children: [
                                  Container(
                                    margin: const EdgeInsets.only(right: 8),
                                    width: 80,
                                    decoration: BoxDecoration(
                                      borderRadius: BorderRadius.circular(8),
                                      image: DecorationImage(
                                        image: FileImage(_fotosTomadas[index]),
                                        fit: BoxFit.cover,
                                      ),
                                    ),
                                  ),
                                  Positioned(
                                    top: 0,
                                    right: 8,
                                    child: GestureDetector(
                                      onTap: () {
                                        setModalState(() {
                                          _fotosTomadas.removeAt(index);
                                        });
                                      },
                                      child: const CircleAvatar(
                                        radius: 10,
                                        backgroundColor: Colors.red,
                                        child: Icon(
                                          Icons.close,
                                          size: 12,
                                          color: Colors.white,
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              );
                            },
                          ),
                        ),
                      ),

                    const SizedBox(height: 24),

                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _isLoading || _isUploadingFotos
                            ? null
                            : () => _enviarEmergencia(context),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFD32F2F),
                          padding: const EdgeInsets.symmetric(vertical: 16),
                        ),
                        child: _isLoading || _isUploadingFotos
                            ? const CircularProgressIndicator(
                                color: Colors.white,
                              )
                            : const Text(
                                'SOLICITAR AUXILIO INMEDIATO',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                      ),
                    ),
                    const SizedBox(height: 32),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: _xOffset,
      top: _yOffset,
      child: GestureDetector(
        // Lógica para arrastrar la burbuja
        onPanUpdate: (details) {
          setState(() {
            // Actualizamos la posición sumando el desplazamiento del dedo
            _xOffset += details.delta.dx;
            _yOffset += details.delta.dy;

            // Opcional: Podrías añadir límites aquí usando MediaQuery
            // para que la burbuja no se salga de la pantalla.
          });
        },
        // Lógica al tocar la burbuja
        onTap: () => _showEmergencySheet(context),
        child: Container(
          width: 65,
          height: 65,
          decoration: BoxDecoration(
            color: const Color(0xFFD32F2F), // Rojo alerta
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: const Color(0xFFD32F2F).withOpacity(0.4),
                blurRadius: 15,
                spreadRadius: 5,
                offset: const Offset(0, 5),
              ),
            ],
            border: Border.all(color: Colors.white, width: 2),
          ),
          child: const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.car_crash, color: Colors.white, size: 28),
                Text(
                  'SOS',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
