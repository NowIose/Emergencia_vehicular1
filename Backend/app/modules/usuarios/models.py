from sqlalchemy import Column, Integer, String, ForeignKey, Float, Enum, Boolean, Table
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class UserRole(enum.Enum):
    ADMIN_TALLER = "admin_taller"
    PERSONAL_TALLER = "personal_taller"
    CLIENTE = "cliente"
    ADMIN_SISTEMA = "admin_sistema"

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    rol = Column(Enum(UserRole), nullable=False)
    
    tipo_perfil = Column(String(50))
    
    __mapper_args__ = {
        "polymorphic_identity": "usuario",
        "polymorphic_on": tipo_perfil,
    }

class Administrador(Usuario):
    __tablename__ = "perfil_administradores"
    id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    nombre_completo = Column(String(100))

    __mapper_args__ = {"polymorphic_identity": "admin"}
    
class Cliente(Usuario):
    __tablename__ = "perfil_clientes"
    id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    nombre = Column(String(100))
    telefono = Column(String(20))
    ci = Column(String(20), nullable=True) 
    fecha_nacimiento = Column(String(50), nullable=True)
    foto_perfil = Column(String(255), nullable=True)
    vehiculos = relationship("app.modules.vehiculos.models.Vehiculo", back_populates="dueno")
    __mapper_args__ = {"polymorphic_identity": "cliente"}

taller_especialidad = Table(
    "taller_especialidad",
    Base.metadata,
    Column("taller_id", Integer, ForeignKey("perfil_talleres.id", ondelete="CASCADE"), primary_key=True),
    Column("especialidad_id", Integer, ForeignKey("especialidades.id", ondelete="CASCADE"), primary_key=True)
)
# 2. MODELO DE ESPECIALIDADES
class Especialidad(Base):
    __tablename__ = "especialidades"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False) # Ej: "Electricidad", "Mecánica General", "Gomería", "Chapa y Pintura"
    descripcion = Column(String(255), nullable=True)

    # Relación inversa (opcional, por si quieres saber qué talleres tienen esta especialidad)
    talleres = relationship("Taller", secondary=taller_especialidad, back_populates="especialidades")

class Taller(Usuario):
    __tablename__ = "perfil_talleres"
    id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    
    # Campos que coinciden con el formulario y tu diagrama
    nombre_taller = Column(String(150), nullable=False)
    telefono = Column(String(20),nullable=True) # Agregado
    nit = Column(String(50), nullable=True) # Agregado
    ciudad = Column(String(100), nullable=True) # Agregado
    direccion = Column(String(255), nullable=True) # Agregado
    foto_perfil = Column(String(255), nullable=True) # URL de la foto (Opcional)
    
    # Para geolocalización (lat/lng)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)

    # NUEVO: Control de acceso por pago
    suscripcion_activa = Column(Boolean, default=False)

    # 3. AGREGAR ESTA RELACIÓN MUCHOS A MUCHOS
    especialidades = relationship("Especialidad", secondary=taller_especialidad, back_populates="talleres")
    personal = relationship("PersonalTaller", back_populates="taller", foreign_keys="PersonalTaller.taller_id")
    __mapper_args__ = {"polymorphic_identity": "taller"}

    
class PersonalTaller(Usuario):
    """ Empleados del taller: mecánicos, electricistas, admins, etc. """
    __tablename__ = "personal_taller"
    
    id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    nombre_completo = Column(String(100))
    cargo = Column(String(50))  # Aquí guardas: "Electricista", "Mecánico", "Ventas"
    especialidad = Column(String(100), nullable=True) 
    foto_perfil = Column(String(255), nullable=True) # URL de la foto (Cloudinary)
    activo = Column(Boolean, default=True)
    
    taller_id = Column(Integer, ForeignKey("perfil_talleres.id"))
    taller = relationship("Taller", back_populates="personal", foreign_keys=[taller_id])
    
    __mapper_args__ = {"polymorphic_identity": "personal_taller"}

from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class CalificacionTaller(Base):
    __tablename__ = "calificaciones_talleres"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("perfil_clientes.id"), nullable=False)
    taller_id = Column(Integer, ForeignKey("perfil_talleres.id"), nullable=False)
    # Relacionarlo con la emergencia es clave para validar que sí lo atendió
    emergencia_id = Column(Integer, nullable=False) # Si tienes una tabla de emergencias, ponle ForeignKey
    
    puntuacion = Column(Float, nullable=False) # Ej: 1.0 a 5.0
    comentario = Column(String(255), nullable=True)
    fecha_calificacion = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    cliente = relationship("Cliente", backref="calificaciones_dadas")
    taller = relationship("Taller", backref="calificaciones_recibidas")



