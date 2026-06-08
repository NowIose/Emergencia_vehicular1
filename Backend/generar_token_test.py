import sys
import os

# Añadir el directorio actual al path para poder importar app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.security import create_access_token
from datetime import timedelta

# ==========================================
# CONFIGURACIÓN DEL TOKEN A GENERAR
# ==========================================
USER_ID = 24  # Pon aquí el ID del usuario cliente (tu caso es el 24)
USER_ROLE = "cliente"
USER_NAME = "Usuario Prueba"
# ==========================================

def generar_token():
    # El payload debe coincidir con lo que espera el backend
    data = {
        "sub": str(USER_ID),
        "rol": USER_ROLE,
        "name": USER_NAME
    }
    
    # Generamos un token que dure 1 hora para pruebas
    token = create_access_token(data=data, expires_delta=timedelta(hours=1))
    
    print("\n" + "="*50)
    print(f"✅ TOKEN GENERADO PARA USUARIO ID: {USER_ID}")
    print(f"🎭 ROL: {USER_ROLE}")
    print("="*50)
    print(f"\n{token}\n")
    print("="*50)
    print("👉 Copia este token y pégalo en 'test_pago_emergencia.py'")
    print("="*50 + "\n")

if __name__ == "__main__":
    generar_token()
