from pydantic import EmailStr, BaseModel
from typing import Optional

class TallerCreate(BaseModel):
    # Datos de la tabla Usuario
    email: EmailStr
    password: str  # Para registro, la contraseña suele ser obligatoria
    telefono: Optional[str] = None
    
    # Datos de la tabla Taller
    nombre_taller: str
    nit: str
    ciudad: str
    direccion: str
    
    # --- ATRIBUTOS QUE FALTABAN ---
    # Los ponemos como Optional para que el registro no falle si el 
    # frontend aún no implementa GPS o Cloudinary
    latitud: Optional[float] = 0.0
    longitud: Optional[float] = 0.0
    foto_perfil: Optional[str] = None 

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


class UsuarioLoginInfo(BaseModel):
    id: int
    email: EmailStr
    rol: str

#Backend responde con TokenResponse(el token Jwt)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UsuarioLoginInfo



#Backend responde con UsuarioResponse(datos del usuario)
class UsuarioResponse(BaseModel):
    id: int
    email: EmailStr
    rol: str
    tipo_perfil: str
    
    class Config:
        from_attributes = True

# --- Esquemas para PersonalTaller ---

class PersonalTallerCreate(BaseModel):
    email: EmailStr
    password: str
    nombre_completo: str
    cargo: str  # E.g., "Mecánico", "Electricista"
    especialidad: Optional[str] = None
    foto_perfil: Optional[str] = None

class PersonalTallerUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    cargo: Optional[str] = None
    especialidad: Optional[str] = None
    foto_perfil: Optional[str] = None
    password: Optional[str] = None
    activo: Optional[bool] = None

class PersonalTallerResponse(BaseModel):
    id: int
    email: EmailStr
    nombre_completo: str
    cargo: str
    especialidad: Optional[str] = None
    foto_perfil: Optional[str] = None
    activo: bool
    taller_id: int
    
    class Config:
        from_attributes = True

