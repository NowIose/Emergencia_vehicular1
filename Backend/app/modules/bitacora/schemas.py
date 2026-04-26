from pydantic import BaseModel
from datetime import date, time
from typing import Optional

class BitacoraBase(BaseModel):
    accion: str
    detalle: Optional[str] = None

class BitacoraCreate(BitacoraBase):
    ip: Optional[str] = None
    agente: Optional[str] = None
    id_usuario: Optional[int] = None
    id_taller: Optional[int] = None

class BitacoraResponse(BitacoraBase):
    id: int
    ip: Optional[str]
    agente: Optional[str]
    hora: time
    fecha: date
    id_usuario: Optional[int]
    id_taller: Optional[int]

    class Config:
        from_attributes = True
