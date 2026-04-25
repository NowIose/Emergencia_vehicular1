import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class EmergenciaService {
  // OJO: Usa 10.0.2.2 para emulador Android, o la IP de tu PC para dispositivo físico.
  final String _baseUrl = dotenv.env['API_URL'] ?? 'http://192.168.1.15:8000';
  final _storage = const FlutterSecureStorage();

  Future<bool> solicitarAuxilio({
    required int idVehiculo,
    required String ubicacion,
    required String descripcion,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          "id_vehiculo": idVehiculo,
          "ubicacion_real": ubicacion,
          "descripcion": descripcion,
          "prioridad": "alta",
        }),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return true; // Éxito
      } else {
        print("Error del servidor: ${response.body}");
        return false;
      }
    } catch (e) {
      print("Error de conexión: $e");
      return false;
    }
  }

  Future<List<dynamic>> getMisEmergencias() async {
    final token = await _storage.read(key: 'jwt_token');

    final response = await http.get(
      Uri.parse("$_baseUrl/emergencias/cliente"),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      final errorBody = jsonDecode(response.body);
      throw Exception(errorBody['detail'] ?? 'Error al obtener emergencias');
    }
  }

  Future<Map<String, dynamic>> calificarEmergencia(
    int nro,
    int puntuacion,
    String comentario,
  ) async {
    final token = await _storage.read(key: 'jwt_token');

    final response = await http.post(
      Uri.parse("$_baseUrl/emergencias/$nro/calificar"),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({'puntuacion': puntuacion, 'comentario': comentario}),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      final errorBody = jsonDecode(response.body);
      throw Exception(errorBody['detail'] ?? 'Error al calificar emergencia');
    }
  }
}
