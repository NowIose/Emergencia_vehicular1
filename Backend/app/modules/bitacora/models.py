from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Bitacora(Base):
    __tablename__ = "bitacora"

    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String(50), nullable=True)
    agente = Column(String(255), nullable=True)
    # Se usan Date y Time por separado como solicitaste
    hora = Column(Time, default=lambda: datetime.now().time())
    fecha = Column(Date, default=lambda: datetime.now().date())
    accion = Column(String(100), nullable=False)
    detalle = Column(String(500), nullable=True)
    
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    id_taller = Column(Integer, ForeignKey("perfil_talleres.id"), nullable=True)

    # Relaciones para obtener información extra si es necesario
    usuario = relationship(
            "app.modules.usuarios.models.Usuario", 
            foreign_keys=[id_usuario]
        )
    taller = relationship(
            "app.modules.usuarios.models.Taller", 
            foreign_keys=[id_taller]
        )