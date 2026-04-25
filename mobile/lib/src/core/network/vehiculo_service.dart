import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class VehiculoService {
  // Si usas el emulador de Android, usa 10.0.2.2. Si es celular físico, tu IP local.
  final String _baseUrl = dotenv.env['API_URL'] ?? 'http://192.168.1.15:8000';
  final _storage = const FlutterSecureStorage();

  Future<void> registrarVehiculo(Map<String, dynamic> vehiculoData) async {
    final token = await _storage.read(key: 'jwt_token');

    final response = await http.post(
      Uri.parse("$_baseUrl/vehiculos/"),
      headers: {
        'Content-Type': 'application/json',
        'Authorization':
            'Bearer $token', // Aquí viaja tu ID de usuario (ej. ID 5)
      },
      body: jsonEncode(vehiculoData),
    );

    if (response.statusCode != 200 && response.statusCode != 201) {
      final errorBody = jsonDecode(response.body);
      throw Exception(errorBody['detail'] ?? 'Error al guardar el vehículo');
    }
  }
}
