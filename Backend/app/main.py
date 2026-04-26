from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.usuarios.routes import router as usuarios_router
# Importar otros módulos cuando los tengas: 
from app.modules.emergencias.routes import router as emergencias_router

from app.modules.usuarios import models as usuarios_models
from app.modules.vehiculos import models as vehiculos_models
from app.modules.emergencias import models as emergencias_models
# ---------------------------------------

from app.modules.usuarios.routes import router as usuarios_router
from app.modules.vehiculos.routes import router as vehiculos_router
# from app.modules.emergencias.routes import router as emergencias_router
from app.modules.emergencias.reportes import router as reportes_router
from app.modules.reportes.routes import router as reportes_admin_router

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
app.include_router(reportes_router)
app.include_router(reportes_admin_router)