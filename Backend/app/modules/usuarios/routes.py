from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.core.database import get_db
from .models import Taller, UserRole, Cliente
from .schemas import TallerCreate, ClienteCreate

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
from .schemas import LoginRequest, TokenResponse, UsuarioResponse
from .services import authenticate_user
from fastapi.security import OAuth2PasswordBearer

from typing import List
from .schemas import TallerResponse

#es un descriptor que le dice a FastAPI donde pedir el token en este caso el endpoint /login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="usuarios/login")

@router.post("/register-taller", status_code=status.HTTP_201_CREATED)
def register_taller(obj_in: TallerCreate, db: Session = Depends(get_db)):
    # ... validación de existencia ...

    nuevo_taller = Taller(
        email=obj_in.email,
        password_hash=pwd_context.hash(obj_in.password),
        rol=UserRole.ADMIN_TALLER,
        tipo_perfil="taller", # Mantén esta línea para la herencia polimórfica
        nombre_taller=obj_in.nombre_taller, # Ahora coinciden ambos lados
        nit=obj_in.nit,
        ciudad=obj_in.ciudad,
        direccion=obj_in.direccion
    )
    
    try:
        db.add(nuevo_taller)
        db.commit()
        db.refresh(nuevo_taller)
        
        # Opcional: Registrar actividad en la bitácora usando tu service
        # registrar_actividad(db, nuevo_taller.id, "Registro de taller nuevo")
        
        return {"message": "Taller registrado", "id": nuevo_taller.id}
    except Exception as e:
        db.rollback() # Siempre haz rollback si falla el commit
        print(f"ERROR REAL: {e}") # Mira esto en la terminal de VS Code
        raise HTTPException(status_code=500, detail=str(e))
    
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Valida el token JWT y devuelve el usuario.
    Se ejecuta automáticamente cuando un endpoint la usa como Depends.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autorizado - token inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodifica el token JWT
        payload = jwt.decode(token, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        user_id: str = payload.get("sub")  # Extrae el user_id del token
        if user_id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
    
    # Busca el usuario en la BD
    user = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica usuario (email + contraseña) y genera token JWT.
    """
    # Llama a authenticate_user de services.py
    user = authenticate_user(db, request.email, request.password)
    
    if not user:
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
    access_token = create_access_token(
        data={
            "sub": str(user.id), 
            "email": user.email, 
            "rol": user.rol.value,
            "name": nombre_usuario  # <--- AGREGAMOS ESTO
        }
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

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