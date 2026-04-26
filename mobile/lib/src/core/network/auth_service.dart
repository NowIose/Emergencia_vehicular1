import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';
import '../../features/auth/domian/user_model.dart';

class AuthService {
  // 1. Asegúrate de que API_URL en el .env NO tenga "/api/v1" al final
  final String _baseUrl = dotenv.env['API_URL'] ?? 'http://192.168.1.3:8000';

  Future<bool> registerUser(RegisterRequest data) async {
    try {
      // 2. La ruta debe empezar directamente con /usuarios
      final response = await http.post(
        Uri.parse(
          '$_baseUrl/usuarios/register-cliente',
        ), // <-- Cambiado de taller a cliente
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(data.toJson()),
      );

      print("URL llamada: ${Uri.parse('$_baseUrl/usuarios/register-taller')}");
      print("Status: ${response.statusCode}");

      return response.statusCode == 201 || response.statusCode == 200;
    } catch (e) {
      print("Error: $e");
      return false;
    }
  }
}
