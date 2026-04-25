import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/network/emergencia_service.dart';
import 'package:intl/intl.dart';
import 'emergencia_detail_screen.dart';

class MisEmergenciasScreen extends StatefulWidget {
  const MisEmergenciasScreen({super.key});

  @override
  State<MisEmergenciasScreen> createState() => _MisEmergenciasScreenState();
}

class _MisEmergenciasScreenState extends State<MisEmergenciasScreen> {
  final EmergenciaService _emergenciaService = EmergenciaService();
  List<dynamic> _pendientes = [];
  List<dynamic> _enProceso = [];
  List<dynamic> _finalizadas = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _cargarEmergencias();
  }

  Future<void> _cargarEmergencias() async {
    try {
      final emergencias = await _emergenciaService.getMisEmergencias();
      if (mounted) {
        setState(() {
          _pendientes = emergencias
              .where((e) => e['estado'].toString().toLowerCase() == 'espera')
              .toList();
          _enProceso = emergencias
              .where(
                (e) => e['estado'].toString().toLowerCase() == 'atendiendo',
              )
              .toList();
          _finalizadas = emergencias
              .where(
                (e) =>
                    e['estado'].toString().toLowerCase() == 'terminado' ||
                    e['estado'].toString().toLowerCase() == 'cancelado',
              )
              .toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error: ${e.toString()}')));
      }
    }
  }

  void _verDetalle(Map<String, dynamic> emergencia) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => EmergenciaDetailScreen(emergencia: emergencia),
      ),
    );
  }

  void _mostrarDialogoCalificacion(BuildContext context, dynamic emer) {
    int ratingSeleccionado = 5; // Valor por defecto
    TextEditingController comentarioController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setStateDialog) {
            return AlertDialog(
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              title: const Text(
                'Calificar Taller',
                textAlign: TextAlign.center,
              ),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('¿Qué tal fue el servicio brindado?'),
                  const SizedBox(height: 16),
                  // Fila de estrellas interactiva
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(5, (index) {
                      return IconButton(
                        icon: Icon(
                          index < ratingSeleccionado
                              ? Icons.star
                              : Icons.star_border,
                          color: Colors.amber,
                          size: 32,
                        ),
                        onPressed: () {
                          setStateDialog(() {
                            ratingSeleccionado = index + 1;
                          });
                        },
                      );
                    }),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: comentarioController,
                    decoration: InputDecoration(
                      hintText: 'Añade un comentario (opcional)',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    maxLines: 2,
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text(
                    'Cancelar',
                    style: TextStyle(color: Colors.grey),
                  ),
                ),
                ElevatedButton(
                  onPressed: () {
                    // Aquí llamas a tu backend POST /calificaciones
                    print(
                      'Enviando calificación de $ratingSeleccionado al taller ${emer['id_taller']}',
                    );
                    // await _emergenciaService.calificarTaller(emer['id_taller'], emer['id'], ratingSeleccionado);
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('¡Gracias por tu calificación!'),
                      ),
                    );
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                  ),
                  child: const Text(
                    'Enviar',
                    style: TextStyle(color: Colors.white),
                  ),
                ),
              ],
            );
          },
        );
      },
    );
  }

  String _formatDate(dynamic dateString) {
    if (dateString == null) return 'Desconocida';
    try {
      DateTime dt = DateTime.parse(dateString.toString());
      return DateFormat('dd MMM, HH:mm').format(dt);
    } catch (e) {
      return dateString.toString();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA), // background color from HTML
      appBar: AppBar(
        title: const Text(
          'Emergency History',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontFamily: 'Manrope',
            color: Color(0xFFB91C1C), // text-red-700
          ),
        ),
        backgroundColor: Colors.white.withOpacity(0.75),
        elevation: 0,
        centerTitle: true,
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: AppColors.primary),
            )
          : RefreshIndicator(
              onRefresh: _cargarEmergencias,
              color: AppColors.primary,
              child: ListView(
                padding: const EdgeInsets.all(20.0),
                children: [
                  if (_pendientes.isNotEmpty) ...[
                    _buildSectionHeader(
                      'Pendientes',
                      '${_pendientes.length} NUEVAS',
                      Colors.amber[800]!,
                      Colors.amber[100]!,
                    ),
                    const SizedBox(height: 16),
                    ..._pendientes.map((e) => _buildPendingCard(e)).toList(),
                    const SizedBox(height: 24),
                  ],

                  if (_enProceso.isNotEmpty) ...[
                    _buildSectionHeader(
                      'En Proceso',
                      '${_enProceso.length} EN CAMINO',
                      Colors.blue[800]!,
                      Colors.blue[100]!,
                    ),
                    const SizedBox(height: 16),
                    ..._enProceso.map((e) => _buildInProgressCard(e)).toList(),
                    const SizedBox(height: 24),
                  ],

                  if (_finalizadas.isNotEmpty) ...[
                    _buildSectionHeader(
                      'Finalizadas',
                      'VER TODO',
                      const Color(0xFFAF101A),
                      Colors.transparent,
                    ),
                    const SizedBox(height: 16),
                    ..._finalizadas.map((e) => _buildCompletedCard(e)).toList(),
                    const SizedBox(height: 80), // bottom padding for FAB
                  ],

                  if (_pendientes.isEmpty &&
                      _enProceso.isEmpty &&
                      _finalizadas.isEmpty)
                    const Center(
                      child: Padding(
                        padding: EdgeInsets.all(40.0),
                        child: Text(
                          'No hay emergencias en tu historial.',
                          style: TextStyle(color: Colors.grey, fontSize: 16),
                        ),
                      ),
                    ),
                ],
              ),
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // Future functionality to add new emergency
        },
        backgroundColor: const Color(0xFFAF101A), // primary-container
        child: const Icon(Icons.add_alert, color: Colors.white),
      ),
    );
  }

  Widget _buildSectionHeader(
    String title,
    String badgeText,
    Color badgeTextColor,
    Color badgeBgColor,
  ) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            fontFamily: 'Manrope',
            color: Color(0xFF191C1D),
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          decoration: BoxDecoration(
            color: badgeBgColor,
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(
            badgeText,
            style: TextStyle(
              color: badgeTextColor,
              fontSize: 10,
              fontWeight: FontWeight.bold,
              fontFamily: 'Manrope',
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPendingCard(dynamic emer) {
    return GestureDetector(
      onTap: () => _verDetalle(emer),
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.amber[100]!.withOpacity(0.5)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'ESPERANDO TALLER',
                        style: TextStyle(
                          color: Colors.amber[600],
                          fontWeight: FontWeight.bold,
                          fontSize: 10,
                          fontFamily: 'Manrope',
                          letterSpacing: 1.2,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        emer['descripcion'] ?? 'Servicio Requerido',
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          fontFamily: 'Manrope',
                          color: Color(0xFF191C1D),
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: Colors.amber[50],
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(Icons.car_crash, color: Colors.amber[600]),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(Icons.schedule, size: 16, color: Colors.grey),
                const SizedBox(width: 8),
                Text(
                  _formatDate(emer['fecha_creacion']),
                  style: const TextStyle(color: Colors.grey, fontSize: 14),
                ),
              ],
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => _verDetalle(emer),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(
                    0xFFE7E8E9,
                  ), // surface-container-high
                  foregroundColor: const Color(0xFF191C1D), // on-surface
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      'Ver Detalles',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontFamily: 'Manrope',
                      ),
                    ),
                    SizedBox(width: 8),
                    Icon(Icons.arrow_forward, size: 16),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInProgressCard(dynamic emer) {
    return GestureDetector(
      onTap: () => _verDetalle(emer),
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.blue[100]!.withOpacity(0.5)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              height: 128,
              width: double.infinity,
              color: Colors.blue[50], // Map placeholder
              child: Stack(
                children: [
                  const Center(
                    child: Icon(Icons.map, size: 48, color: Colors.blue),
                  ),
                  Positioned(
                    bottom: 12,
                    left: 12,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.9),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 8,
                            height: 8,
                            decoration: const BoxDecoration(
                              color: Colors.blue,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 8),
                          const Text(
                            'Taller en camino',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              emer['id_taller'] != null
                                  ? 'TALLER ASIGNADO #${emer['id_taller']}'
                                  : 'TALLER ASIGNADO',
                              style: TextStyle(
                                color: Colors.blue[600],
                                fontWeight: FontWeight.bold,
                                fontSize: 10,
                                fontFamily: 'Manrope',
                                letterSpacing: 1.2,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              emer['descripcion'] ?? 'Falla reportada',
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                fontFamily: 'Manrope',
                                color: Color(0xFF191C1D),
                              ),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        ),
                      ),
                      Container(
                        width: 48,
                        height: 48,
                        decoration: BoxDecoration(
                          color: Colors.blue[50],
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Icon(
                          Icons.build_circle,
                          color: Colors.blue[600],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      const Icon(
                        Icons.calendar_today,
                        size: 16,
                        color: Colors.grey,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        _formatDate(emer['fecha_creacion']),
                        style: const TextStyle(
                          color: Colors.grey,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () => _verDetalle(emer),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(
                          0xFFAF101A,
                        ), // primary-container
                        foregroundColor: Colors.white,
                        elevation: 2,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                      child: const Text(
                        'Ver Detalles del Servicio',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontFamily: 'Manrope',
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCompletedCard(dynamic emer) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.green!.withOpacity(0.5)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'SERVICIO COMPLETADO',
                      style: TextStyle(
                        color: Colors.green,
                        fontWeight: FontWeight.bold,
                        fontSize: 10,
                        fontFamily: 'Manrope',
                        letterSpacing: 1.2,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      emer['descripcion'] ?? 'Falla reparada',
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        fontFamily: 'Manrope',
                        color: Color(0xFF191C1D),
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: Colors.green,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(Icons.check_circle, color: Colors.green),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // Botones de acción
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () => _verDetalle(emer),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: const Color(0xFF191C1D),
                    side: BorderSide(color: Colors.grey!),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: const Text('Ver Detalles'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () {
                    // Abrir un modal para calificar al taller
                    _mostrarDialogoCalificacion(context, emer);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.amber,
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  icon: const Icon(Icons.star, size: 18),
                  label: const Text(
                    'Calificar',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
