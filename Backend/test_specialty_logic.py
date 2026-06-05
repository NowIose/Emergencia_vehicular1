import asyncio
import os
import sys
from sqlalchemy.orm import Session

# Configurar path
sys.path.append(os.path.join(os.getcwd(), "Backend"))

from app.core.database import SessionLocal
from app.modules.emergencias.routes import pre_analizar_emergencia
from app.modules.emergencias import schemas

async def test_logic():
    db = SessionLocal()
    try:
        # Mocking req
        req = schemas.PreAnalisisRequest(
            descripcion="Mi auto no arranca y huele a quemado cerca de la batería",
            ubicacion_cliente="-17.7833,-63.1821", # Cerca del taller central del seed
            radio_km=10.0
        )
        
        print("Testing pre-analizar endpoint...")
        # Nota: Esto llamará a la IA real si hay llaves en el .env
        res = await pre_analizar_emergencia(req, db)
        
        print("\n--- RESULTADO DEL ANÁLISIS ---")
        print(f"Diagnóstico: {res.diagnostico}")
        print(f"Prioridad: {res.prioridad}")
        print(f"Especialidad Detectada: {res.especialidad_ia}")
        print(f"Talleres sugeridos encontrados: {len(res.talleres_sugeridos)}")
        
        for t in res.talleres_sugeridos:
            print(f"- {t.nombre_taller} ({t.distancia_km} km) - Especialidades: {t.especialidades}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("GROQ_API_KEY"):
        print("⚠️ No hay API KEYS detectadas. El test podría fallar si no hay mocks.")
    asyncio.run(test_logic())
