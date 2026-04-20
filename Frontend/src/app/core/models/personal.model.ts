export interface PersonalTaller {
  id?: number;
  email: string;
  password?: string; // Solo para creación
  nombre_completo: string;
  cargo: string;
  especialidad?: string;
  foto_perfil?: string;
  activo: boolean;
  taller_id: number;
}