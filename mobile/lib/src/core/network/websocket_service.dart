// lib/services/websocket_service.dart
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class WebSocketService {
  WebSocketChannel? _channel;

  final String _baseUrl = dotenv.env['API_URL'] ?? 'http://10.0.2.2:8000';

  String get _wsUrl {
    // Esto cambia https:// -> wss:// o http:// -> ws:// automáticamente
    return _baseUrl.replaceFirst('https', 'wss').replaceFirst('http', 'ws');
  }
  // Conexión para el TALLER
  void connectTaller(Function(Map<String, dynamic>) onMessage) {
    _channel = WebSocketChannel.connect(Uri.parse("$_wsUrl/taller"));
    _listen(onMessage);
  }

  // Conexión para el CLIENTE
  void connectCliente(int clientId, Function(Map<String, dynamic>) onMessage) {
    _channel = WebSocketChannel.connect(
      Uri.parse("$_wsUrl/cliente/$clientId"),
    );
    _listen(onMessage);
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
  }
}
