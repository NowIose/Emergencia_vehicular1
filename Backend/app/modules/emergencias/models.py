from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

# 1. Enums para integridad de datos
class PrioridadEmergencia(str, enum.Enum):
    alta = "alta"
    media = "media"
    baja = "baja"

class EstadoEmergencia(str, enum.Enum):
    espera = "espera"
    atendiendo = "atendiendo"
    cancelado = "cancelado"
    terminado = "terminado"

# 2. Modelo Principal de Emergencia
class Emergencia(Base):
    __tablename__ = "emergencias"
    
    nro = Column(Integer, primary_key=True, index=True)
    ubicacion_real = Column(String, comment="Coordenadas GPS del lugar del incidente") 
    fotos = Column(JSON, nullable=True) # Lista de URLs de Cloudinary
    audio = Column(String, nullable=True) # URL de audio de Cloudinary
    descripcion = Column(String(500))
    
    prioridad = Column(SQLEnum(PrioridadEmergencia), default=PrioridadEmergencia.media)
    estado = Column(SQLEnum(EstadoEmergencia), default=EstadoEmergencia.espera)
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Claves Foráneas corregidas según tus modelos de usuarios
    id_vehiculo = Column(Integer, ForeignKey("vehiculos.id"), nullable=False)
    # Apunta a la tabla personal_taller que me pasaste
    id_personal = Column(Integer, ForeignKey("personal_taller.id"), nullable=True) 

    # Relaciones
    # Nota: Asegúrate que en vehiculos/models.py exista el back_populates="emergencias"
    vehiculo = relationship("app.modules.vehiculos.models.Vehiculo", back_populates="emergencias")
    
    # Relación con el personal que atiende (PersonalTaller)
    personal = relationship("app.modules.usuarios.models.PersonalTaller")
    
    # Relación uno a uno con el detalle de seguimiento
    detalles = relationship("DetalleEmergencia", back_populates="emergencia", uselist=False)

# 3. Seguimiento en Tiempo Real (Geolocalización dinámica)
class DetalleEmergencia(Base):
    __tablename__ = "detalle_emergencias"
    
    id = Column(Integer, primary_key=True, index=True)
    nro_emergencia = Column(Integer, ForeignKey("emergencias.nro"), unique=True)
    
    tiempo_llegada_estimado = Column(String(50), nullable=True) # Ej: "10 min"
    ubicacion_personal_real = Column(String, nullable=True, comment="Ubicación GPS actual del mecánico") 

    emergencia = relationship("Emergencia", back_populates="detalles")

# 4. Mensajería (Chat Taller <-> Cliente)
class Mensajeria(Base):
    __tablename__ = "mensajeria"
    
    id = Column(Integer, primary_key=True, index=True)
    nro_emergencia = Column(Integer, ForeignKey("emergencias.nro"), nullable=False)
    
    # Polimorfismo: id_remitente puede ser el ID del Cliente o del Taller (Admin)
    id_remitente = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    mensaje = Column(String(1000), nullable=False)
    fecha_hora = Column(DateTime, default=datetime.utcnow)
    leido = Column(Boolean, default=False)

    # Relación para saber quién envió el mensaje sin importar su rol
    remitente = relationship("app.modules.usuarios.models.Usuario")