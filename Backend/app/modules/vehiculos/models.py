# app/modules/vehiculos/models.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Vehiculo(Base):
    __tablename__ = "vehiculos"
    
    id = Column(Integer, primary_key=True)
    placa = Column(String(20), unique=True, index=True) # Muy importante para identificar el auto
    marca = Column(String(50))
    modelo = Column(String(50))
    color = Column(String(30))
    anio = Column(Integer)
    
    # El dueño es un Cliente
    cliente_id = Column(Integer, ForeignKey("perfil_clientes.id"))
    dueno = relationship("app.modules.usuarios.models.Cliente", back_populates="vehiculos")
    
    # Un vehículo puede estar en muchas emergencias a lo largo del tiempo
    emergencias = relationship("app.modules.emergencias.models.Emergencia", back_populates="vehiculo")