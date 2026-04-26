import sys
import os

# Añadir el directorio actual al path para que encuentre 'app'
sys.path.append(os.getcwd())

try:
    from app.main import app
    print("✅ App imports successfully")
    from app.modules.usuarios.routes import router as usuarios_router
    print("✅ Usuarios routes import successfully")
    from app.modules.bitacora.utils import registrar_evento
    print("✅ Bitacora utils import successfully")
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
