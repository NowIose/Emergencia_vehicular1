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
// NUEVO IMPORT QUIRÚRGICO
import '../../../emergencies/presentation/pages/workshop_selection_screen.dart';

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
  // --- Variables para Speech-to-Text ---
  final stt.SpeechToText _speechToText = stt.SpeechToText();
  bool _speechEnabled = false;
  String _lastWords = '';

  @override
  void initState() {
    super.initState();
    _vehiculoSeleccionado = widget.idVehiculoSeleccionado;
    _initSpeech();
    // Sincronizar alertas pendientes guardadas en offline
    _sincronizarEmergenciasPendientes();
  }

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
             // Aseguramos que el ID sea int
            var firstId = _misVehiculos.first['id'];
            _vehiculoSeleccionado = firstId is int ? firstId : int.tryParse(firstId.toString());
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

  // 3. Subir fotos al backend
  Future<List<String>> _subirFotos() async {
    List<String> urls = [];
    final urlUpload = Uri.parse('$_baseUrl/usuarios/upload-image');
    const storage = FlutterSecureStorage();
    String? token = await storage.read(key: 'jwt_token');

    for (File foto in _fotosTomadas) {
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
        debugPrint("Error subiendo foto: $e");
      }
    }
    return urls;
  }

  // 4. Función para obtener GPS
  Future<void> _obtenerUbicacion() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Por favor habilita el GPS')));
      return;
    }
    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) return;
    }
    Position position = await Geolocator.getCurrentPosition();
    setState(() {
      _ubicacionActual = '${position.latitude}, ${position.longitude}';
    });
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('📍 Ubicación capturada con éxito')));
  }

  // 5. FUNCIÓN ENVIAR (MODIFICADA QUIRÚRGICAMENTE PARA PRE-ANÁLISIS)
  Future<void> _enviarEmergencia(BuildContext context) async {
    if (_descripcionController.text.isEmpty || _ubicacionActual == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Añade descripción y ubicación')));
      return;
    }
    if (_vehiculoSeleccionado == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Selecciona un vehículo')));
      return;
    }

    setState(() => _isLoading = true);

    try {
      List<String> fotosUrls = [];
      if (_fotosTomadas.isNotEmpty) {
        setState(() => _isUploadingFotos = true);
        fotosUrls = await _subirFotos();
        setState(() => _isUploadingFotos = false);
      }

      const storage = FlutterSecureStorage();
      String? token = await storage.read(key: 'jwt_token');

      // PASO 1: LLAMAR AL NUEVO ENDPOINT DE PRE-ANÁLISIS
      final urlPre = Uri.parse('$_baseUrl/emergencias/pre-analizar');
      final responsePre = await http.post(
        urlPre,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          if (token != null) 'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          "descripcion": _descripcionController.text,
          "ubicacion_cliente": _ubicacionActual,
          "fotos": fotosUrls,
          "radio_km": 2.0 
        }),
      ).timeout(const Duration(seconds: 15));

      if (responsePre.statusCode == 200) {
        final dataPre = jsonDecode(responsePre.body);
        
        if (mounted) {
          // PASO 2: NAVEGAR AL MAPA DE SELECCIÓN (MAPBOX)
          final int? tallerSeleccionadoId = await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => WorkshopSelectionScreen(
                diagnostico: dataPre['diagnostico'],
                prioridad: dataPre['prioridad'],
                especialidad: dataPre['especialidad_ia'],
                talleres: dataPre['talleres_sugeridos'],
                ubicacionCliente: _ubicacionActual!,
              ),
            ),
          );

          // PASO 3: SI SELECCIONÓ TALLER, CREAR EMERGENCIA DEFINITIVA
          if (tallerSeleccionadoId != null) {
            final urlCreate = Uri.parse('$_baseUrl/emergencias/');
            final responseFinal = await http.post(
              urlCreate,
              headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                if (token != null) 'Authorization': 'Bearer $token',
              },
              body: jsonEncode({
                "id_vehiculo": _vehiculoSeleccionado,
                "ubicacion_real": _ubicacionActual,
                "descripcion": _descripcionController.text,
                "prioridad": dataPre['prioridad'],
                "fotos": fotosUrls,
                "id_taller": tallerSeleccionadoId
              }),
            );

            if (responseFinal.statusCode >= 200 && responseFinal.statusCode < 300) {
              if (mounted) Navigator.pop(context); 
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('🚨 Alerta enviada al taller con éxito')));
              _limpiarFormulario();
            }
          }
        }
      } else {
        // FALLBACK: Si falla el pre-análisis (Online pero con error de IA), enviamos el flujo normal (broadcast)
        await _enviarFlujoDirecto(fotosUrls);
      }
    } on SocketException {
      // CAPTURA OFFLINE: Sigue funcionando igual que antes
      await _guardarEmergenciaLocal();
    } catch (e) {
      debugPrint("Error en envío: $e");
      await _guardarEmergenciaLocal();
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _limpiarFormulario() {
    _descripcionController.clear();
    _ubicacionActual = null;
    _fotosTomadas.clear();
  }

  // El flujo original de envío directo que ya tenías
  Future<void> _enviarFlujoDirecto(List<String> fotosUrls) async {
    const storage = FlutterSecureStorage();
    String? token = await storage.read(key: 'jwt_token');
    final url = Uri.parse('$_baseUrl/emergencias/');

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
    ).timeout(const Duration(seconds: 10));

    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (mounted) Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('🚨 Alerta enviada exitosamente')));
      _limpiarFormulario();
      _sincronizarEmergenciasPendientes();
    }
  }

  // LÓGICA OFFLINE (RESTAURADA TOTALMENTE)
  Future<void> _guardarEmergenciaLocal() async {
    try {
      const storage = FlutterSecureStorage();
      String? pendientesStr = await storage.read(key: 'emergencias_pendientes');
      List<dynamic> pendientes = (pendientesStr != null) ? jsonDecode(pendientesStr) : [];

      pendientes.add({
        "id_vehiculo": _vehiculoSeleccionado,
        "ubicacion_real": _ubicacionActual,
        "descripcion": _descripcionController.text,
        "prioridad": "alta",
        "fotos_locales": _fotosTomadas.map((f) => f.path).toList(),
        "fecha_creacion": DateTime.now().toIso8601String(),
      });

      await storage.write(key: 'emergencias_pendientes', value: jsonEncode(pendientes));

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('📴 Sin internet. Auxilio guardado localmente.'),
          backgroundColor: Colors.orange,
        ));
        Navigator.pop(context);
        _limpiarFormulario();
      }
    } catch (e) {
      debugPrint("Error al guardar caché offline: $e");
    }
  }

  Future<void> _sincronizarEmergenciasPendientes() async {
    const storage = FlutterSecureStorage();
    String? pendientesStr = await storage.read(key: 'emergencias_pendientes');
    if (pendientesStr == null || pendientesStr == '[]') return;

    List<dynamic> pendientes = jsonDecode(pendientesStr);
    List<dynamic> noEnviados = [];
    String? token = await storage.read(key: 'jwt_token');

    for (var em in pendientes) {
      try {
        List<String> urls = await _subirFotosOffline(em['fotos_locales'] ?? []);
        final resp = await http.post(
          Uri.parse('$_baseUrl/emergencias/'),
          headers: {'Content-Type': 'application/json', if (token != null) 'Authorization': 'Bearer $token'},
          body: jsonEncode({
            "id_vehiculo": em["id_vehiculo"],
            "ubicacion_real": em["ubicacion_real"],
            "descripcion": em["descripcion"],
            "prioridad": em["prioridad"],
            "fotos": urls,
          }),
        );
        if (resp.statusCode >= 200 && resp.statusCode < 300) {
          debugPrint("✅ Offline sincronizado");
        } else {
          noEnviados.add(em);
        }
      } catch (e) {
        noEnviados.add(em);
        break;
      }
    }
    await storage.write(key: 'emergencias_pendientes', value: jsonEncode(noEnviados));
  }

  Future<List<String>> _subirFotosOffline(List<dynamic> paths) async {
    List<String> urls = [];
    final urlUpload = Uri.parse('$_baseUrl/usuarios/upload-image');
    const storage = FlutterSecureStorage();
    String? token = await storage.read(key: 'jwt_token');

    for (dynamic path in paths) {
      File foto = File(path.toString());
      if (!await foto.exists()) continue;

      var request = http.MultipartRequest('POST', urlUpload);
      request.files.add(await http.MultipartFile.fromPath('file', foto.path, contentType: MediaType('image', 'jpeg')));
      request.fields['folder'] = 'emergencia_vehicular/emergencias';
      request.headers.addAll({'Accept': 'application/json', if (token != null) 'Authorization': 'Bearer $token'});

      try {
        var response = await request.send();
        var respStr = await response.stream.bytesToString();
        if (response.statusCode == 201 || response.statusCode == 200) {
          urls.add(jsonDecode(respStr)['url']);
        }
      } catch (e) { rethrow; }
    }
    return urls;
  }

  // SPEECH TO TEXT (RESTAURADO TOTALMENTE)
  void _startListening(StateSetter setModalState) async {
    await _speechToText.listen(
      onResult: (result) {
        setModalState(() {
          _descripcionController.text = result.recognizedWords;
          _descripcionController.selection = TextSelection.fromPosition(TextPosition(offset: _descripcionController.text.length));
        });
      },
      localeId: 'es_ES',
    );
    setModalState(() {});
  }

  void _stopListening(StateSetter setModalState) async {
    await _speechToText.stop();
    setModalState(() {});
  }

  void _showEmergencySheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (context) {
        return StatefulBuilder(
          builder: (BuildContext context, StateSetter setModalState) {
            if (_misVehiculos.isEmpty) {
              _cargarMisVehiculos(setModalState);
            }

            return Padding(
              padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom, left: 24, right: 24, top: 24),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Solicitar Auxilio', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.red)),
                    const SizedBox(height: 16),

                    // Selector de Vehículo (FIX Dropdown Error)
                    if (_misVehiculos.isNotEmpty)
                      DropdownButtonFormField<int>(
                        decoration: InputDecoration(
                          filled: true,
                          fillColor: Colors.grey.shade100,
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                          hintText: 'Selecciona tu vehículo',
                        ),
                        // FIX: Asegurar que el value coincida exactamente con uno de los IDs de los items
                        value: _misVehiculos.any((v) {
                          final id = v['id'] is int ? v['id'] : int.tryParse(v['id'].toString());
                          return id == _vehiculoSeleccionado;
                        }) ? _vehiculoSeleccionado : null,
                        items: _misVehiculos.map((v) {
                          final int? id = v['id'] is int ? v['id'] : int.tryParse(v['id'].toString());
                          return DropdownMenuItem<int>(
                            value: id,
                            child: Text('${v['marca']} ${v['modelo']} - ${v['placa']}'),
                          );
                        }).toList(),
                        onChanged: (val) {
                          setModalState(() {
                            _vehiculoSeleccionado = val;
                          });
                        },
                      )
                    else
                      const Center(child: Padding(padding: EdgeInsets.all(8.0), child: CircularProgressIndicator())),

                    const SizedBox(height: 16),

                    TextField(
                      controller: _descripcionController,
                      maxLines: 3,
                      decoration: InputDecoration(
                        hintText: _speechToText.isListening ? 'Escuchando...' : '¿Qué le ocurrió a tu vehículo?',
                        filled: true, fillColor: Colors.grey.shade200,
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                        suffixIcon: IconButton(
                          icon: Icon(_speechToText.isListening ? Icons.mic : Icons.mic_none, color: _speechToText.isListening ? Colors.red : Colors.grey.shade600, size: 28),
                          onPressed: () {
                            if (!_speechEnabled) return;
                            if (_speechToText.isNotListening) { _startListening(setModalState); } else { _stopListening(setModalState); }
                          },
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    Row(
                      children: [
                        Expanded(child: OutlinedButton.icon(onPressed: () => _tomarFoto(setModalState), icon: const Icon(Icons.camera_alt), label: Text('Foto (${_fotosTomadas.length}/3)'))),
                        const SizedBox(width: 12),
                        Expanded(child: OutlinedButton.icon(onPressed: () async { await _obtenerUbicacion(); setModalState(() {}); }, icon: Icon(_ubicacionActual != null ? Icons.check_circle : Icons.location_on, size: 20, color: _ubicacionActual != null ? Colors.green : null), label: Text(_ubicacionActual != null ? 'GPS Listo' : 'Ubicación'))),
                      ],
                    ),
                    const SizedBox(height: 24),

                    if (_fotosTomadas.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 8.0),
                        child: SizedBox(
                          height: 80,
                          child: ListView.builder(
                            scrollDirection: Axis.horizontal,
                            itemCount: _fotosTomadas.length,
                            itemBuilder: (context, index) {
                              return Stack(children: [
                                Container(margin: const EdgeInsets.only(right: 8), width: 80, decoration: BoxDecoration(borderRadius: BorderRadius.circular(8), image: DecorationImage(image: FileImage(_fotosTomadas[index]), fit: BoxFit.cover))),
                                Positioned(top: 0, right: 8, child: GestureDetector(onTap: () => setModalState(() => _fotosTomadas.removeAt(index)), child: const CircleAvatar(radius: 10, backgroundColor: Colors.red, child: Icon(Icons.close, size: 12, color: Colors.white)))),
                              ]);
                            },
                          ),
                        ),
                      ),

                    const SizedBox(height: 24),

                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _isLoading || _isUploadingFotos ? null : () => _enviarEmergencia(context),
                        style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFD32F2F), padding: const EdgeInsets.symmetric(vertical: 16)),
                        child: _isLoading || _isUploadingFotos ? const CircularProgressIndicator(color: Colors.white) : const Text('SOLICITAR AUXILIO INMEDIATO', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
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
      left: _xOffset, top: _yOffset,
      child: GestureDetector(
        onPanUpdate: (details) => setState(() { _xOffset += details.delta.dx; _yOffset += details.delta.dy; }),
        onTap: () => _showEmergencySheet(context),
        child: Container(
          width: 65, height: 65,
          decoration: BoxDecoration(color: const Color(0xFFD32F2F), shape: BoxShape.circle, boxShadow: [BoxShadow(color: const Color(0xFFD32F2F).withOpacity(0.4), blurRadius: 15, spreadRadius: 5, offset: const Offset(0, 5))], border: Border.all(color: Colors.white, width: 2)),
          child: const Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(Icons.car_crash, color: Colors.white, size: 28), Text('SOS', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold))])),
        ),
      ),
    );
  }
}
