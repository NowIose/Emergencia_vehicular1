from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
# Importa tu Base de datos. Ajusta esta ruta a donde tengas definido tu Base = declarative_base()
from app.core.database import Base 

class BackupCloud(Base):
    __tablename__ = "backups_cloud"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), index=True)
    url = Column(String(500))
    key_r2 = Column(String(255))
    tamano = Column(Float) # Guardamos el tamaño en MB
    fecha_creacion = Column(DateTime, default=datetime.utcnow)