from pydantic import EmailStr, BaseModel
from typing import Optional

class TallerCreate(BaseModel):
    # Datos de la tabla Usuario
    email: EmailStr
    password: Optional[str] = None
    telefono: str
    
    # Datos de la tabla Taller
    nombre_taller: str
    nit: str
    ciudad: str
    direccion: str
    
    class Config:
        from_attributes = True

class ClienteCreate(BaseModel):
    email: EmailStr
    password: str
    nombre: str
    telefono: str
    ci: str
    fecha_nacimiento: Optional[str] = None
    class Config:
        from_attributes = True


'''
Frontend → POST /login con LoginRequest
                    ↓
Backend procesa, crea token
                    ↓
Backend → Responde con TokenResponse (el token JWT)
                    ↓
Frontend guarda en localStorage
                    ↓
Frontend → GET /me con el token en header
                    ↓
Backend → Responde con UsuarioResponse (datos del usuario)
'''
#Frontend envia datos JSON Post/login con loginRequest
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

#Backend responde con TokenResponse(el token Jwt)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

#Backend responde con UsuarioResponse(datos del usuario)
class UsuarioResponse(BaseModel):
    id: int
    email: EmailStr
    rol: str
    tipo_perfil: str
    
    class Config:
        from_attributes = True

class TallerResponse(BaseModel):
    id: int
    email: EmailStr
    nombre_taller: str
    ciudad: str
    direccion: str
    foto_perfil: Optional[str] = None
    
    class Config:
        from_attributes = True