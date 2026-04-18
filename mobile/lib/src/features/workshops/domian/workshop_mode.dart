class WorkshopModel {
  final int id;
  final String nombreTaller;
  final String ciudad;
  final String direccion;
  final String? fotoPerfil;

  WorkshopModel({
    required this.id,
    required this.nombreTaller,
    required this.ciudad,
    required this.direccion,
    this.fotoPerfil,
  });

  factory WorkshopModel.fromJson(Map<String, dynamic> json) {
    return WorkshopModel(
      id: json['id'],
      nombreTaller: json['nombre_taller'] ?? 'Taller sin nombre',
      ciudad: json['ciudad'] ?? '',
      direccion: json['direccion'] ?? 'Ubicación no disponible',
      fotoPerfil: json['foto_perfil'],
    );
  }
}
