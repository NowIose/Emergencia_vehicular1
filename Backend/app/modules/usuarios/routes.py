from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.core.database import get_db
from .models import Taller, UserRole, Cliente
from .schemas import TallerCreate, ClienteCreate
from app.modules.bitacora.utils import registrar_evento

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])
#pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") #como que este no es necesario
#Lo importare desde security.py para evitar duplicación de código
from app.core.security import pwd_context



#IMPORTS NUEVOS JOSE
import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from app.core.security import create_access_token, verify_password

from .models import Usuario
from .schemas import LoginRequest, TokenResponse, UsuarioResponse, PersonalTallerCreate, PersonalTallerUpdate, PersonalTallerResponse, TallerResponse
from .services import authenticate_user, create_personal_taller, get_personal_by_taller, update_personal_taller, delete_personal_taller, get_personal_by_id, create_taller_service
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List
from pydantic import BaseModel


#es un descriptor que le dice a FastAPI donde pedir el token en este caso el endpoint /login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="usuarios/login")

@router.post("/register-taller", status_code=status.HTTP_201_CREATED)
def register_taller(obj_in: TallerCreate, fastapi_request: Request, db: Session = Depends(get_db)):
    # 1. Verificar si el email ya existe
    user_exists = db.query(Usuario).filter(Usuario.email == obj_in.email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    try:
        # 2. Llamar al servicio que acabamos de crear
        nuevo_taller = create_taller_service(db, obj_in)
        
        # Registrar en bitácora
        registrar_evento(db, fastapi_request, "Registro de Taller", f"Nuevo taller registrado: {obj_in.nombre_taller} ({obj_in.email})")
        
        return {"message": "Taller registrado exitosamente", "id": nuevo_taller.id}
    except Exception as e:
        print(f"ERROR EN REGISTRO: {e}")
        #raise HTTPException(status_code=500, detail="Error interno al registrar el taller")
        raise HTTPException(status_code=500, detail=str(e))

    
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autorizado - token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. Intenta decodificar con la lista de algoritmos
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            print("ERROR: El token no tiene campo 'sub'")
            raise credentials_exception
            
    except jwt.ExpiredSignatureError:
        print("ERROR: El token ha expirado")
        raise HTTPException(status_code=401, detail="El token ha expirado")
    except jwt.InvalidTokenError as e:
        print(f"ERROR DE JWT: {e}")
        raise credentials_exception
    except Exception as e:
        print(f"ERROR INESPERADO: {e}")
        raise credentials_exception
    print(f"TOKEN DECODIFICADO CORRECTAMENTE, USER ID: {user_id}")

    # 2. Busca en la base de datos
    user = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if user is None:
        print(f"ERROR: Usuario con ID {user_id} no existe en la DB")
        raise credentials_exception
        
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    fastapi_request: Request,
    # form_data: OAuth2PasswordRequestForm = Depends(),  #ACTIVA ESTO SI QUIERES USAR EL FORMULARIO ESTÁNDAR DE OAuth2 (con campos 'username' y 'password')
    db: Session = Depends(get_db)):
    """
    Autentica usuario (email + contraseña) y genera token JWT.
    """
    # Llama a authenticate_user de services.py
    user = authenticate_user(db, login_data.email, login_data.password) # Cambia login_data.email por form_data.username si usas el formulario estándar de OAuth2
    
    if not user:
        # Registrar intento fallido
        registrar_evento(db, fastapi_request, "Inicio de sesión fallido", f"Intento con email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 2. Lógica para extraer el NOMBRE real según el perfil
    nombre_usuario = "Usuario"
    
    if user.tipo_perfil == "cliente":
        # Buscamos en la tabla de clientes
        cliente = db.query(Cliente).filter(Cliente.id == user.id).first()
        nombre_usuario = cliente.nombre if cliente else "Cliente"
    elif user.tipo_perfil == "taller":
        # Buscamos en la tabla de talleres
        taller = db.query(Taller).filter(Taller.id == user.id).first()
        nombre_usuario = taller.nombre_taller if taller else "Taller"
    elif user.tipo_perfil == "admin":
        nombre_usuario = "Administrador"

    access_token = create_access_token(
        data={
            "sub": str(user.id), 
            "email": user.email, 
            "rol": user.rol.value,
            "name": nombre_usuario  # <--- AGREGAMOS ESTO
        }
    )
    
    # Registrar inicio de sesión exitoso
    registrar_evento(db, fastapi_request, "Inicio de sesión", f"Usuario {user.email} ha iniciado sesión", usuario=user)

    return {              # "access_token": access_token, "token_type": "bearer"
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "rol": user.rol.value,
            "nombre": nombre_usuario,
            "tipo_perfil": user.tipo_perfil}
        }

@router.get("/me", response_model=UsuarioResponse)
def read_users_me(current_user: Usuario = Depends(get_current_user)):
    """
    Devuelve datos del usuario autenticado.
    Requiere token JWT válido en header Authorization.
    """
    return current_user

@router.post("/register-cliente", status_code=status.HTTP_201_CREATED)
def register_cliente(obj_in: ClienteCreate, db: Session = Depends(get_db)):
    # Verificar si ya existe
    if db.query(Usuario).filter(Usuario.email == obj_in.email).first():
        raise HTTPException(status_code=400, detail="El email ya existe")

    nuevo_cliente = Cliente(
        email=obj_in.email,
        password_hash=pwd_context.hash(obj_in.password),
        rol=UserRole.CLIENTE,
        tipo_perfil="cliente",
        nombre=obj_in.nombre,
        telefono=obj_in.telefono,
        ci=obj_in.ci,
        fecha_nacimiento=obj_in.fecha_nacimiento,
    )
    
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    return {"message": "Cliente registrado", "id": nuevo_cliente.id}

@router.get("/lista-talleres", response_model=List[TallerResponse])
def get_all_talleres(db: Session = Depends(get_db)):
    """
    Devuelve la lista de todos los talleres registrados.
    """
    talleres = db.query(Taller).all()
    return talleres
'''┌─ IMPORTS (todo arriba)
├─ router = APIRouter(...)
├─ oauth2_scheme = OAuth2PasswordBearer(...)
│
├─ @router.post("/register-taller")   ← YA EXISTE
│  def register_taller():
│      ...
│
├─ def get_current_user():  ← NUEVO - función auxiliar
│      ...
│
├─ @router.post("/login")   ← NUEVO
│  def login():
│      ...
│
└─ @router.get("/me")       ← NUEVO
   def read_users_me():
       ...
'''
# --- RUTAS PARA PERSONAL TALLER ---

@router.post("/personal", response_model=PersonalTallerResponse, status_code=status.HTTP_201_CREATED)
def crear_personal(
    obj_in: PersonalTallerCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Permite al administrador del taller registrar un nuevo empleado."""
    if current_user.rol != UserRole.ADMIN_TALLER:
        raise HTTPException(status_code=403, detail="Solo los administradores de taller pueden crear personal")
    
    """Verificar que el email no exista en la base de datos general de usuarios."""
    if db.query(Usuario).filter(Usuario.email == obj_in.email).first():
        raise HTTPException(status_code=400, detail="El email ya existe")
    # El taller_id del administrador es su propio ID (ya que el perfil Taller hereda de Usuario)
    return create_personal_taller(db, obj_in, taller_id=current_user.id)

@router.get("/personal", response_model=List[PersonalTallerResponse])
def listar_personal(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista a todo el personal de este taller."""
    if current_user.rol != UserRole.ADMIN_TALLER:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver esta lista")
        
    return get_personal_by_taller(db, taller_id=current_user.id)

@router.put("/personal/{personal_id}", response_model=PersonalTallerResponse)
def actualizar_personal(
    personal_id: int,
    obj_in: PersonalTallerUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza datos de un empleado."""
    db_obj = get_personal_by_id(db, personal_id)
    if not db_obj or db_obj.taller_id != current_user.id:
        raise HTTPException(status_code=404, detail="Empleado no encontrado o no pertenece a tu taller")
        
    return update_personal_taller(db, db_obj, obj_in)

@router.delete("/personal/{personal_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_personal(
    personal_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina a un empleado de la base de datos."""
    db_obj = get_personal_by_id(db, personal_id)
    if not db_obj or db_obj.taller_id != current_user.id:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
        
    delete_personal_taller(db, personal_id)
    return None


'''PARA CLOUDINARY, CREARÉ UN NUEVO SERVICIO EN cloudinary_service.py PARA MANTENER EL CÓDIGOS LIMPIO Y ORGANIZADO.
y creare en aca routes su end endpoint para subir imagenes y otro para eliminar'''

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from .cloudinary_service import CloudinaryService

@router.post("/upload-image", status_code=status.HTTP_201_CREATED)
async def upload_image_view(
    file: UploadFile = File(...), 
    folder: str = Form("emergencia_vehicular/perfiles")
):
    """
    Endpoint para subir imágenes a Cloudinary.
    Equivalente a tu UploadImageView de Django.
    """
    # 1. Validar que sea una imagen
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="El archivo enviado no es una imagen válida."
        )
    
    try:
        # 2. Llamar al servicio asíncrono que creamos
        data = await CloudinaryService.upload_image(file, folder=folder)
        return data
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(exc)
        )
    except Exception as e:
        print(f"Error interno: {e}") # Para debug en consola
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Error al procesar la imagen en el servidor."
        )
    
class DeleteImageRequest(BaseModel):
    public_id: str

@router.post("/delete-image")
async def delete_image_view(request: DeleteImageRequest):
    """
    Endpoint para eliminar imágenes de Cloudinary.
    """
    try:
        result = await CloudinaryService.delete_image(request.public_id)
        
        # Cloudinary devuelve {'result': 'ok'} si se borró correctamente
        if result.get("result") == "ok":
            return {"message": "Imagen eliminada correctamente"}
        else:
            return {"message": "La imagen no existía o ya fue eliminada", "details": result}
            
    except Exception as e:
        print(f"Error al borrar imagen: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo eliminar la imagen del servidor"
        )