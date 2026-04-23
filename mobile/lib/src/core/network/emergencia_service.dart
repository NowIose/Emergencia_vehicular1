import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';

class EmergenciaService {
  // OJO: Usa 10.0.2.2 para emulador Android, o la IP de tu PC para dispositivo físico.
  final String _baseUrl = dotenv.env['API_URL'] ?? 'http://192.168.1.15:8000';

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
}
