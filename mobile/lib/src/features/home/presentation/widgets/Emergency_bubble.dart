import 'dart:io';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http_parser/http_parser.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

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
  // --- NUEVO: Variables para Speech-to-Text ---
  final stt.SpeechToText _speechToText = stt.SpeechToText();
  bool _speechEnabled = false;
  String _lastWords = '';
  @override
  void initState() {
    super.initState();
    _vehiculoSeleccionado = widget.idVehiculoSeleccionado;
    _initSpeech(); // --- NUEVO ---
    // Intentar sincronizar alertas pendientes guardadas en offline al arrancar la pantalla
    _sincronizarEmergenciasPendientes();
  }

  // --- NUEVO: Función para inicializar el micrófono ---
  void _initSpeech() async {
    _speechEnabled = await _speechToText.initialize(
      onError: (val) => print('Error en S2T: $val'),
      onStatus: (val) => print('Estado S2T: $val'),
    );
    setState(() {});
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

    const storage = FlutterSecureStorage();
    String? token = await storage.read(key: 'jwt_token');

    for (File foto in _fotosTomadas) {
      var request = http.MultipartRequest('POST', urlUpload);

      // --- CAMBIO AQUÍ: Forzar el tipo MIME a image/jpeg ---
      request.files.add(
        await http.MultipartFile.fromPath(
          'file',
          foto.path,
          contentType: MediaType(
            'image',
            'jpeg',
          ), // Le dice a FastAPI que es una imagen segura
        ),
      );

      request.fields['folder'] = 'emergencia_vehicular/emergencias';

      request.headers.addAll({
        'Accept': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      });

      try {
        var response = await request.send();
        var respStr = await response.stream.bytesToString();

        if (response.statusCode == 201 || response.statusCode == 200) {
          var jsonResp = jsonDecode(respStr);
          urls.add(jsonResp['url']);
        } else {
          debugPrint("❌ Error al subir foto. Status: ${response.statusCode}");
          debugPrint("❌ Body de respuesta: $respStr");
        }
      } catch (e) {
        debugPrint("❌ Excepción de red al subir foto: $e");
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

  // 5. Función para enviar al Backend (MODIFICADA CON MANEJO OFFLINE)
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
      // Intentar procesar flujo normal (Online)
      List<String> fotosUrls = [];
      if (_fotosTomadas.isNotEmpty) {
        setState(() => _isUploadingFotos = true);
        fotosUrls = await _subirFotos();
        setState(() => _isUploadingFotos = false);
      }

      const storage = FlutterSecureStorage();
      String? token = await storage.read(key: 'jwt_token');
      final url = Uri.parse('$_baseUrl/emergencias/');

      final response = await http
          .post(
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
          )
          .timeout(
            const Duration(seconds: 10),
          ); // Timeout para forzar captura si la red está colgada

      if (response.statusCode >= 200 && response.statusCode < 300) {
        if (mounted) Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('🚨 Alerta enviada exitosamente')),
        );
        _descripcionController.clear();
        _ubicacionActual = null;
        _fotosTomadas.clear();

        // Aprovechar que recuperó señal para vaciar cualquier otra alerta pendiente previa
        _sincronizarEmergenciasPendientes();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error ${response.statusCode}: ${response.body}'),
          ),
        );
      }
    } on SocketException catch (e) {
      // 🚨 PRINT DE CONTROL
      print("🚨 INSTANCIA DETECTADA: SocketException (Celular sin internet).");
      print("Detalle del error: $e");
      // CAPTURA DE FALTA DE INTERNET: Guardar localmente de inmediato
      await _guardarEmergenciaLocal();
    } catch (e) {
      // 🚨 PRINT DE CONTROL
      print("🚨 INSTANCIA DETECTADA: Otro tipo de error de red.");
      print("Detalle: $e");
      // Otras excepciones de red (ej. Tiempos de espera agotados)
      await _guardarEmergenciaLocal();
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // --- NUEVA FUNCIÓN: Guarda la emergencia localmente si no hay internet ---
  Future<void> _guardarEmergenciaLocal() async {
    try {
      const storage = FlutterSecureStorage();
      String? pendientesStr = await storage.read(key: 'emergencias_pendientes');
      List<dynamic> pendientes = [];

      if (pendientesStr != null && pendientesStr.isNotEmpty) {
        pendientes = jsonDecode(pendientesStr);
      }

      // Estructuramos el payload offline guardando las rutas de los archivos locales
      Map<String, dynamic> nuevaEmergenciaOffline = {
        "id_vehiculo": _vehiculoSeleccionado,
        "ubicacion_real": _ubicacionActual,
        "descripcion": _descripcionController.text,
        "prioridad": "alta",
        "fotos_locales": _fotosTomadas.map((f) => f.path).toList(),
        "fecha_creacion": DateTime.now().toIso8601String(),
      };

      pendientes.add(nuevaEmergenciaOffline);
      await storage.write(
        key: 'emergencias_pendientes',
        value: jsonEncode(pendientes),
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              '📴 Sin internet. Auxilio guardado localmente, se enviará al conectar.',
            ),
            backgroundColor: Colors.orange,
            duration: Duration(seconds: 5),
          ),
        );
        Navigator.pop(context);
        _descripcionController.clear();
        _ubicacionActual = null;
        _fotosTomadas.clear();
      }
    } catch (e) {
      debugPrint("Error al guardar caché offline: $e");
    }
  }

  // --- NUEVA FUNCIÓN: Sube fotos almacenadas localmente durante el modo offline ---
  Future<List<String>> _subirFotosOffline(List<dynamic> paths) async {
    List<String> urls = [];
    final urlUpload = Uri.parse('$_baseUrl/usuarios/upload-image');
    const storage = FlutterSecureStorage();
    String? token = await storage.read(key: 'jwt_token');

    for (dynamic path in paths) {
      File foto = File(path.toString());
      if (!await foto.exists())
        continue; // Si el archivo temporal ya no existe, lo salta

      var request = http.MultipartRequest('POST', urlUpload);
      request.files.add(
        await http.MultipartFile.fromPath(
          'file',
          foto.path,
          contentType: MediaType('image', 'jpeg'),
        ),
      );
      request.fields['folder'] = 'emergencia_vehicular/emergencias';
      request.headers.addAll({
        'Accept': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      });

      try {
        var response = await request.send();
        var respStr = await response.stream.bytesToString();
        if (response.statusCode == 201 || response.statusCode == 200) {
          var jsonResp = jsonDecode(respStr);
          urls.add(jsonResp['url']);
        }
      } catch (e) {
        debugPrint("Error subiendo foto en background: $e");
        rethrow; // Propaga el error para detener la sincronización de este registro si falla la red
      }
    }
    return urls;
  }

  // --- NUEVA FUNCIÓN: Proceso de sincronización en segundo plano ---
  Future<void> _sincronizarEmergenciasPendientes() async {
    const storage = FlutterSecureStorage();
    String? pendientesStr = await storage.read(key: 'emergencias_pendientes');

    if (pendientesStr == null ||
        pendientesStr.isEmpty ||
        pendientesStr == '[]') {
      return;
    }

    debugPrint(
      "🔄 Detectadas emergencias offline pendientes por sincronizar...",
    );
    List<dynamic> pendientes = jsonDecode(pendientesStr);
    List<dynamic> noEnviados = [];

    String? token = await storage.read(key: 'jwt_token');
    final url = Uri.parse('$_baseUrl/emergencias/');

    for (var emergencia in pendientes) {
      try {
        List<String> fotosUrls = [];
        List<dynamic> fotosLocales = emergencia['fotos_locales'] ?? [];

        // 1. Subir las fotos locales si existen rutas guardadas
        if (fotosLocales.isNotEmpty) {
          fotosUrls = await _subirFotosOffline(fotosLocales);
        }

        // 2. Enviar el reporte definitivo al backend
        final response = await http.post(
          url,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            if (token != null) 'Authorization': 'Bearer $token',
          },
          body: jsonEncode({
            "id_vehiculo": emergencia["id_vehiculo"],
            "ubicacion_real": emergencia["ubicacion_real"],
            "descripcion": emergencia["descripcion"],
            "prioridad": emergencia["prioridad"],
            "fotos": fotosUrls,
          }),
        );

        if (response.statusCode >= 200 && response.statusCode < 300) {
          debugPrint("✅ Emergencia offline sincronizada correctamente.");
        } else {
          // Si el servidor responde con error de validación, mantenlo para no perder el dato
          noEnviados.add(emergencia);
        }
      } catch (e) {
        // Si vuelve a fallar la conexión, conservamos la emergencia en la cola
        debugPrint(
          "❌ Falló el intento de sincronización local (sigue sin red): $e",
        );
        noEnviados.add(emergencia);
        break; // Detiene el bucle para evitar reintentos innecesarios en este ciclo
      }
    }

    // Actualizar el almacenamiento con lo que quedó pendiente o vacío si todo se envió
    await storage.write(
      key: 'emergencias_pendientes',
      value: jsonEncode(noEnviados),
    );
  }

  // --- NUEVO: Iniciar escucha ---
  // Recibe setModalState para poder actualizar la UI del BottomSheet (cambiar el ícono a rojo)
  void _startListening(StateSetter setModalState) async {
    await _speechToText.listen(
      onResult: (result) {
        setModalState(() {
          // Actualizamos el campo de texto con lo que va escuchando
          _descripcionController.text = result.recognizedWords;
          // Coloca el cursor al final del texto
          _descripcionController.selection = TextSelection.fromPosition(
            TextPosition(offset: _descripcionController.text.length),
          );
        });
      },
      localeId:
          'es_ES', // Fuerza el idioma a español (puedes ajustarlo si prefieres otro)
    );
    setModalState(() {});
  }

  // --- NUEVO: Detener escucha ---
  void _stopListening(StateSetter setModalState) async {
    await _speechToText.stop();
    setModalState(() {});
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

                    // --- MODIFICADO: TextField con botón de micrófono ---
                    TextField(
                      controller: _descripcionController,
                      maxLines: 3,
                      decoration: InputDecoration(
                        hintText: _speechToText.isListening
                            ? 'Escuchando...'
                            : '¿Qué le ocurrió a tu vehículo?',
                        filled: true,
                        fillColor: Colors.grey.shade200,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide.none,
                        ),
                        // Añadimos el ícono del micrófono a la derecha
                        suffixIcon: IconButton(
                          icon: Icon(
                            _speechToText.isListening
                                ? Icons.mic
                                : Icons.mic_none,
                            color: _speechToText.isListening
                                ? Colors.red
                                : Colors.grey.shade600,
                            size: 28,
                          ),
                          onPressed: () {
                            // Verificamos si los permisos fueron concedidos
                            if (!_speechEnabled) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text(
                                    'El reconocimiento de voz no está disponible.',
                                  ),
                                ),
                              );
                              return;
                            }

                            // Alternar entre escuchar y detener
                            if (_speechToText.isNotListening) {
                              _startListening(setModalState);
                            } else {
                              _stopListening(setModalState);
                            }
                          },
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
