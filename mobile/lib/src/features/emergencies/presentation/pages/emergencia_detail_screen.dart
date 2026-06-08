import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import 'package:intl/intl.dart';
import '../../../../core/network/emergencia_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:jwt_decoder/jwt_decoder.dart';
import 'package:url_launcher/url_launcher.dart';

class EmergenciaDetailScreen extends StatefulWidget {
  final Map<String, dynamic> emergencia;

  const EmergenciaDetailScreen({super.key, required this.emergencia});

  @override
  State<EmergenciaDetailScreen> createState() => _EmergenciaDetailScreenState();
}

class _EmergenciaDetailScreenState extends State<EmergenciaDetailScreen> {
  final EmergenciaService _emergenciaService = EmergenciaService();
  final _storage = const FlutterSecureStorage();
  bool _isCalificando = false;
  String? _userRole;
  Map<String, dynamic>? _pagoInfo;
  bool _isLoadingPago = true;

  @override
  void initState() {
    super.initState();
    _loadUserData();
    _loadPagoInfo();
  }

  Future<void> _loadUserData() async {
    String? token = await _storage.read(key: 'jwt_token');
    if (token != null && !JwtDecoder.isExpired(token)) {
      Map<String, dynamic> decodedToken = JwtDecoder.decode(token);
      setState(() {
        _userRole = decodedToken['rol'];
      });
    }
  }

  Future<void> _loadPagoInfo() async {
    try {
      final info = await _emergenciaService.getPaymentInfo(widget.emergencia['nro']);
      setState(() {
        _pagoInfo = info;
        _isLoadingPago = false;
      });
    } catch (e) {
      setState(() => _isLoadingPago = false);
    }
  }

  void _mostrarDialogoSetPrecio() {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Fijar Precio del Servicio'),
        content: TextField(
          controller: controller,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(
            labelText: 'Monto (USD)',
            prefixIcon: Icon(Icons.attach_money),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
          ElevatedButton(
            onPressed: () async {
              double? monto = double.tryParse(controller.text);
              if (monto != null) {
                try {
                  await _emergenciaService.setEmergenciaPrecio(widget.emergencia['nro'], monto);
                  Navigator.pop(context);
                  _loadPagoInfo();
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Precio fijado con éxito')));
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
                }
              }
            },
            child: const Text('Guardar'),
          ),
        ],
      ),
    );
  }

  Future<void> _iniciarPagoStripe() async {
    try {
      final url = await _emergenciaService.payEmergencia(widget.emergencia['nro']);
      final uri = Uri.parse(url);
      
      // Intentar abrir de la forma más compatible
      if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
        throw 'No se pudo abrir la pasarela de pago';
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error al iniciar pago: $e')));
    }
  }

  void _mostrarDialogoCalificacion() {
    int puntuacion = 5;
    TextEditingController comentarioController = TextEditingController();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return StatefulBuilder(
          builder: (BuildContext context, StateSetter setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                bottom: MediaQuery.of(context).viewInsets.bottom,
                left: 20,
                right: 20,
                top: 20,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Calificar Servicio',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      fontFamily: 'Manrope',
                      color: AppColors.onSurface,
                    ),
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    '¿Qué tal fue el servicio brindado por el taller?',
                    style: TextStyle(color: AppColors.onSurfaceVariant),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(5, (index) {
                      return IconButton(
                        icon: Icon(
                          index < puntuacion ? Icons.star : Icons.star_border,
                          color: Colors.amber,
                          size: 40,
                        ),
                        onPressed: () {
                          setModalState(() {
                            puntuacion = index + 1;
                          });
                        },
                      );
                    }),
                  ),
                  const SizedBox(height: 20),
                  TextField(
                    controller: comentarioController,
                    maxLines: 3,
                    decoration: InputDecoration(
                      hintText: 'Escribe un comentario (opcional)',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: const BorderSide(color: AppColors.primary),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFAF101A),
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      onPressed: _isCalificando
                          ? null
                          : () async {
                              setModalState(() {
                                _isCalificando = true;
                              });
                              try {
                                await _emergenciaService.calificarEmergencia(
                                  widget.emergencia['nro'],
                                  puntuacion,
                                  comentarioController.text,
                                );
                                Navigator.pop(context); // cerrar modal
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(
                                    content: Text(
                                      '¡Gracias por tu calificación!',
                                    ),
                                  ),
                                );
                              } catch (e) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text('Error: $e')),
                                );
                              } finally {
                                setModalState(() {
                                  _isCalificando = false;
                                });
                              }
                            },
                      child: _isCalificando
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(
                                color: Colors.white,
                                strokeWidth: 2,
                              ),
                            )
                          : const Text(
                              'Enviar Calificación',
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontFamily: 'Manrope',
                                fontSize: 16,
                              ),
                            ),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    // Parsing date if available
    String fecha = 'Desconocida';
    if (widget.emergencia['fecha_creacion'] != null) {
      try {
        DateTime dt = DateTime.parse(widget.emergencia['fecha_creacion']);
        fecha = DateFormat('dd/MM/yyyy HH:mm').format(dt);
      } catch (e) {
        fecha = widget.emergencia['fecha_creacion'].toString();
      }
    }

    final String estado = (widget.emergencia['estado'] ?? '')
        .toString()
        .toUpperCase();
    final String prioridad = (widget.emergencia['prioridad'] ?? 'NORMAL')
        .toString()
        .toUpperCase();
    final List<dynamic> fotos = widget.emergencia['fotos'] ?? [];

    // Si la emergencia está terminada, podemos mostrar el FAB para calificar
    final bool canRate = estado == 'TERMINADO';

    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        title: const Text(
          'Detalle de Emergencia',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontFamily: 'Manrope',
            color: Color(0xFFB91C1C),
          ),
        ),
        backgroundColor: AppColors.surface,
        elevation: 0,
        iconTheme: const IconThemeData(color: Color(0xFF191C1D)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header Info
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Emergencia #${widget.emergencia['nro']}',
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    fontFamily: 'Manrope',
                    color: Color(0xFF191C1D),
                  ),
                ),
                _buildBadge(estado, _getColorByEstado(estado)),
              ],
            ),
            const SizedBox(height: 20),

            // Info Cards
            _buildInfoRow(
              Icons.description,
              'Descripción',
              widget.emergencia['descripcion'] ?? 'Sin descripción',
            ),
            _buildInfoRow(
              Icons.location_on,
              'Ubicación',
              widget.emergencia['ubicacion_real'] ?? 'Ubicación desconocida',
            ),
            _buildInfoRow(Icons.calendar_today, 'Fecha', fecha),
            _buildInfoRow(
              Icons.warning,
              'Prioridad',
              prioridad,
              color: prioridad == 'ALTA' ? Colors.red : Colors.orange,
            ),
            _buildInfoRow(
              Icons.directions_car,
              'ID Vehículo',
              widget.emergencia['id_vehiculo']?.toString() ?? 'N/A',
            ),
            if (widget.emergencia['nombre_taller'] != null)
              _buildInfoRow(
                Icons.home_repair_service,
                'Taller Asignado',
                widget.emergencia['nombre_taller'].toString(),
              )
            else if (widget.emergencia['id_taller'] != null)
              _buildInfoRow(
                Icons.build,
                'ID Taller Asignado',
                widget.emergencia['id_taller'].toString(),
              ),
              
            if (widget.emergencia['detalles'] != null && 
                widget.emergencia['detalles']['tiempo_llegada_estimado'] != null)
              _buildInfoRow(
                Icons.access_time,
                'Tiempo Estimado de Llegada',
                widget.emergencia['detalles']['tiempo_llegada_estimado'].toString(),
                color: Colors.blue,
              ),

            const SizedBox(height: 30),

            // --- SECCIÓN DE PAGO ---
            if (!_isLoadingPago) ...[
              const Text(
                'Información de Pago',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  fontFamily: 'Manrope',
                  color: Color(0xFF191C1D),
                ),
              ),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.grey[300]!),
                ),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Costo del Servicio:', style: TextStyle(fontWeight: FontWeight.w500)),
                        const SizedBox(width: 8),
                        Flexible(
                          child: Text(
                            _pagoInfo != null ? '\$${(_pagoInfo!['monto'] / 100).toStringAsFixed(2)} ${_pagoInfo!['moneda'].toUpperCase()}' : 'Pendiente',
                            textAlign: TextAlign.right,
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: _pagoInfo != null ? Colors.green[700] : Colors.grey,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const Divider(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Estado del Pago:'),
                        _buildBadge(
                          _pagoInfo != null && _pagoInfo!['pagado'] ? 'PAGADO' : 'PENDIENTE',
                          _pagoInfo != null && _pagoInfo!['pagado'] ? Colors.green : Colors.orange,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Botón para el Taller (Fijar Precio)
              if ((_userRole == 'admin_taller' || _userRole == 'personal_taller') && (_pagoInfo == null || !_pagoInfo!['pagado']))
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: _mostrarDialogoSetPrecio,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue[800],
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    icon: const Icon(Icons.edit),
                    label: Text(_pagoInfo == null ? 'FIJAR PRECIO DEL SERVICIO' : 'ACTUALIZAR PRECIO'),
                  ),
                ),

              // Botón para el Cliente (Pagar con Stripe)
              if (_userRole == 'cliente' && estado == 'TERMINADO' && _pagoInfo != null && !_pagoInfo!['pagado'])
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: _iniciarPagoStripe,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF6772E5), // Stripe Blue
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    icon: const Icon(Icons.credit_card),
                    label: const Text('PAGAR CON STRIPE', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  ),
                ),
              const SizedBox(height: 30),
            ],

            // Photos Section
            if (fotos.isNotEmpty) ...[
              const Text(
                'Fotos Adjuntas',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  fontFamily: 'Manrope',
                  color: Color(0xFF191C1D),
                ),
              ),
              const SizedBox(height: 10),
              SizedBox(
                height: 120,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: fotos.length,
                  itemBuilder: (context, index) {
                    return Container(
                      margin: const EdgeInsets.only(right: 10),
                      width: 120,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(12),
                        image: DecorationImage(
                          image: NetworkImage(fotos[index]),
                          fit: BoxFit.cover,
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
            const SizedBox(height: 80),
          ],
        ),
      ),
      floatingActionButton: canRate
          ? FloatingActionButton.extended(
              onPressed: _mostrarDialogoCalificacion,
              backgroundColor: Colors.amber[600],
              icon: const Icon(Icons.star, color: Colors.white),
              label: const Text(
                'Calificar Servicio',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontFamily: 'Manrope',
                ),
              ),
            )
          : null,
    );
  }

  Widget _buildInfoRow(
    IconData icon,
    String title,
    String value, {
    Color? color,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: (color ?? const Color(0xFFB91C1C)).withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
              icon,
              color: color ?? const Color(0xFFB91C1C),
              size: 24,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.onSurfaceVariant,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 16,
                    color: AppColors.onSurface,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Color _getColorByEstado(String estado) {
    switch (estado.toLowerCase()) {
      case 'espera':
        return Colors.orange;
      case 'atendiendo':
        return Colors.blue;
      case 'terminado':
        return Colors.green;
      case 'cancelado':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  Widget _buildBadge(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.bold,
          fontFamily: 'Manrope',
        ),
      ),
    );
  }
}
