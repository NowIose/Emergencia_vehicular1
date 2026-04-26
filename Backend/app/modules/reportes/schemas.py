from pydantic import BaseModel, EmailStr
from typing import Optional

class ReporteUsuarioDetalle(BaseModel):
    id: int
    email: EmailStr
    rol: str
    nombre: str
    extra: Optional[str] = None  # Aquí irá la calificación o el teléfono
    fecha_registro: Optional[str] = None

    class Config:
        from_attributes = True