from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.modules.vehiculos.schemas import VehiculoResponse

class EmergenciaCreate(BaseModel):
    id_vehiculo: int
    ubicacion_real: str
    descripcion: str
    prioridad: str  # Opcional
    fotos: Optional[List[str]] = None

class DetalleEmergenciaResponse(BaseModel):
    tiempo_llegada_estimado: Optional[str] = None
    ubicacion_personal_real: Optional[str] = None
    class Config:
        from_attributes = True

class EmergenciaResponse(BaseModel):
    nro: int
    ubicacion_real: str
    descripcion: str
    prioridad: str
    estado: str
    fotos: Optional[List[str]] = None
    diagnostico_ia: Optional[str] = None
    fecha_creacion: datetime
    id_vehiculo: int
    id_taller: Optional[int] = None
    nombre_taller: Optional[str] = None
    id_personal: Optional[int] = None
    vehiculo: Optional[VehiculoResponse] = None
    detalles: Optional[DetalleEmergenciaResponse] = None

    class Config:
        from_attributes = True

class AceptarEmergenciaRequest(BaseModel):
    id_personal: int

class EstadoUpdateRequest(BaseModel):
    estado: str
    estado: str

# --- Schemas de Mensajería ---
# 1. Lo que recibimos cuando el Cliente o el Taller envían un mensaje
class MensajeCreate(BaseModel):
    mensaje: str

# 2. Lo que devolvemos al frontend/app móvil (para el historial de chat)
class MensajeResponse(BaseModel):
    id: int
    nro_emergencia: int
    id_remitente: int
    mensaje: str
    fecha_hora: datetime
    leido: bool

    class Config:
        from_attributes = True  # Permite a Pydantic leer el modelo de SQLAlchemy

# 3. Schema opcional por si necesitas actualizar estados de lectura masivos
class MarcarLeidosRequest(BaseModel):
    id_remitente_a_marcar: int

class ReporteEmergenciaResponse(BaseModel):
    etiqueta: str # Puede ser "2026-04-25" (Día) o "2026-04" (Mes)
    total: int

    class Config:
        from_attributes = True
class CalificarEmergenciaRequest(BaseModel):
    puntuacion: float
    comentario: Optional[str] = None
    class Config:
        from_attributes = True