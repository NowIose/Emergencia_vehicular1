from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.usuarios.routes import router as usuarios_router
# Importar otros módulos cuando los tengas: 
from app.modules.emergencias.routes import router as emergencias_router

from app.modules.usuarios import models as usuarios_models
from app.modules.vehiculos import models as vehiculos_models
from app.modules.emergencias import models as emergencias_models
from app.modules.bitacora import models as bitacora_models
# ---------------------------------------

from app.modules.usuarios.routes import router as usuarios_router
from app.modules.vehiculos.routes import router as vehiculos_router
from app.modules.bitacora.routes import router as bitacora_router
# from app.modules.emergencias.routes import router as emergencias_router
from app.modules.emergencias.reportes import router as reportes_router
from app.modules.reportes.routes import router as reportes_admin_router
from app.core.database import SessionLocal 
from app.modules.usuarios.backups.services import generar_backup_en_nube
from app.modules.usuarios.backups.routes import router as backups_router

def tarea_backup_diario():
    print("Iniciando backup automático hacia R2 de las 7:00 AM...")
    db = SessionLocal()
    try:
        generar_backup_en_nube(db)
        print("Backup automático completado con éxito.")
    except Exception as e:
        print(f"Error al generar backup automático: {e}")
    finally:
        db.close() # Siempre cerrar la sesión
app = FastAPI(title="Emergencia Vehicular API")
# Configurar quién tiene permiso de hablar con el servidor
origins = [
    "http://localhost:4200",  # Tu app de Angular
    "http://127.0.0.1:4200",
]
app.add_middleware(
CORSMiddleware,
    allow_origins=["*"],  # Permite todas las URLs (¡cuidado en producción!)
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # Permite todos los encabezados
)

# Registramos el módulo de usuarios
app.include_router(usuarios_router)
app.include_router(vehiculos_router)
app.include_router(emergencias_router)
app.include_router(bitacora_router)
app.include_router(reportes_router)
app.include_router(reportes_admin_router)
app.include_router(backups_router)