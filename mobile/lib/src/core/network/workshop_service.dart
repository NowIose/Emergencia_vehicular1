import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../features/workshops/domian/workshop_mode.dart';

class WorkshopService {
  // OJO: Si pruebas en el emulador de Android, usa 10.0.2.2 en lugar de localhost
  final String baseUrl = 'http://192.168.1.10:8000/usuarios/lista-talleres';

  Future<List<WorkshopModel>> getWorkshops() async {
    try {
      final response = await http.get(Uri.parse(baseUrl));

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
