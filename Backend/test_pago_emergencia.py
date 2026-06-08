import requests
import json
import sys

# ==========================================
# CONFIGURACIÓN DE LA PRUEBA
# ==========================================
# Cambia esta URL si tu backend corre en otro puerto o IP
BASE_URL = "http://localhost:8000" 

# --- INSTRUCCIONES ---
# 1. Inicia sesión en la App como Cliente
# 2. Copia el token JWT (puedes verlo en los logs del backend o de la app)
# 3. Pégalo aquí abajo:
TOKEN_CLIENTE = "TU_TOKEN_JWT_AQUI" 

# El número de emergencia que insertaste manualmente (ej: 66)
NRO_EMERGENCIA = 66
# ==========================================

def probar_pago_emergencia():
    print(f"\n🚀 Probando flujo de pago para Emergencia #{NRO_EMERGENCIA}...")
    
    url = f"{BASE_URL}/pagos/emergencia/pagar"
    
    headers = {
        "Authorization": f"Bearer {TOKEN_CLIENTE}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "nro_emergencia": NRO_EMERGENCIA
    }

    try:
        # 1. Llamada al endpoint para crear la sesión de Stripe
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            checkout_url = data.get('checkout_url')
            session_id = data.get('session_id')
            
            print("\n✅ SESIÓN DE STRIPE CREADA EXITOSAMENTE")
            print(f"📌 Session ID: {session_id}")
            print(f"🔗 URL DE PAGO: {checkout_url}")
            
            print("\n" + "="*50)
            print("PASOS PARA COMPLETAR LA PRUEBA:")
            print("1. Asegúrate de tener el webhook corriendo:")
            print("   stripe listen --forward-to localhost:8000/pagos/webhook")
            print("2. Abre la URL de arriba en tu navegador.")
            print("3. Paga usando la tarjeta de prueba: 4242 4242 4242 4242")
            print("4. Verifica en la base de datos:")
            print(f"   SELECT pagado, fecha_pago FROM pagos_emergencia WHERE nro_emergencia = {NRO_EMERGENCIA};")
            print("="*50 + "\n")
            
        elif response.status_code == 404:
            print(f"\n❌ ERROR: No se encontró información de pago para la emergencia {NRO_EMERGENCIA}.")
            print("Asegúrate de haber insertado el registro en la tabla 'pagos_emergencia'.")
        elif response.status_code == 403:
            print("\n❌ ERROR: Token inválido o el usuario no es el dueño de la emergencia.")
        else:
            print(f"\n❌ ERROR ({response.status_code}): {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: No se pudo conectar al servidor en {BASE_URL}.")
        print("Asegúrate de que el Backend esté corriendo.")
    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    if TOKEN_CLIENTE == "TU_TOKEN_JWT_AQUI":
        print("\n⚠️  ATENCIÓN: Debes poner un TOKEN_CLIENTE válido en el script.")
        print("Puedes obtenerlo del log del backend al iniciar sesión en la app.")
        sys.exit(1)
        
    probar_pago_emergencia()
