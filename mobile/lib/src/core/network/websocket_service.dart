import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class WebSocketService {
  WebSocketChannel? _channel;
  
  // Obtenemos la URL del .env. 
  // Si API_URL es http://192.168.1.15:8000, 
  // el WS será ws://192.168.1.15:8000/emergencias/ws
  String get _wsBaseUrl {
    final baseUrl = dotenv.env['API_URL'] ?? 'http://10.0.2.2:8000';
    return baseUrl.replaceFirst('http', 'ws') + '/emergencias/ws';
  }

 /* String get _wsUrl {
    // Esto cambia https:// -> wss:// o http:// -> ws:// automáticamente
    return _baseUrl.replaceFirst('https', 'wss').replaceFirst('http', 'ws');
  }*/
  // Conexión para el TALLER
  void connectTaller(Function(Map<String, dynamic>) onMessage) {
    print("Conectando WS Taller a: $_wsBaseUrl/taller");
    _channel = WebSocketChannel.connect(Uri.parse("$_wsBaseUrl/taller"));
    _listen(onMessage);
  }

  // Conexión para el CLIENTE
  void connectCliente(int clientId, Function(Map<String, dynamic>) onMessage) {
    print("Conectando WS Cliente $clientId a: $_wsBaseUrl/cliente/$clientId");
    _channel = WebSocketChannel.connect(
      Uri.parse("$_wsBaseUrl/cliente/$clientId"),
    );
    _listen(onMessage);
  }

  // MÉTODO PARA ENVIAR MENSAJES
  void sendMessage(Map<String, dynamic> message) {
    if (_channel != null) {
      _channel!.sink.add(jsonEncode(message));
    } else {
      print("No se puede enviar mensaje: WS desconectado");
    }
  }

  void _listen(Function(Map<String, dynamic>) onMessage) {
    _channel?.stream.listen(
      (data) {
        final decodedData = jsonDecode(data);
        onMessage(decodedData);
      },
      onError: (error) => print("Error WS: $error"),
      onDone: () => print("WS Desconectado"),
    );
  }

  void disconnect() {
    _channel?.sink.close();
    _channel = null;
  }
}
