import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';
import '../../features/auth/domian/user_model.dart';

class AuthService {
  // 1. Asegúrate de que API_URL en el .env NO tenga "/api/v1" al final
  final String _baseUrl = dotenv.env['API_URL'] ?? 'http://192.168.1.14:8000';

  Future<bool> registerUser(RegisterRequest data) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/usuarios/register-cliente'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(data.toJson()),
      );
      return response.statusCode == 201 || response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<bool> registerTaller(Map<String, dynamic> data) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/usuarios/register-taller'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(data),
      );
      return response.statusCode == 201 || response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
