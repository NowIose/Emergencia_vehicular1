import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../features/workshops/domian/workshop_model.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class WorkshopService {
  // OJO: Si pruebas en el emulador de Android, usa 10.0.2.2 en lugar de localhost
  final String baseUrl = dotenv.env['API_URL'] ?? 'URL_NO_ENCONTRADA';
  Future<List<WorkshopModel>> getWorkshops() async {
    final String _baseUrl = '$baseUrl/usuarios/lista-talleres';
    try {
      final response = await http.get(Uri.parse(_baseUrl));

      if (response.statusCode == 200) {
        // Asegúrate de importar dart:convert para jsonDecode
        List<dynamic> body = jsonDecode(response.body);
        return body
            .map((dynamic item) => WorkshopModel.fromJson(item))
            .toList();
      } else {
        throw Exception('Fallo al cargar los talleres');
      }
    } catch (e) {
      throw Exception('Error de conexión: $e');
    }
  }
}
