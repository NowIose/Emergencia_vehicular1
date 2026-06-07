from sqlalchemy.orm import Session
from sqlalchemy import func
from app.modules.usuarios import models as user_models
import httpx
import json
import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def obtener_reporte_usuarios(db: Session, rol_filtro: str = None, orden: str = None):
    query = db.query(user_models.Usuario)
    
    # Filtro de Rol con manejo de Enum para evitar Error 500
    if rol_filtro and rol_filtro.strip():
        try:
            rol_enum = user_models.UserRole[rol_filtro.upper()]
            query = query.filter(user_models.Usuario.rol == rol_enum)
        except KeyError:
            pass
        
    usuarios = query.all()
    resultado = []
    
    for u in usuarios:
        data = {
            "id": u.id,
            "email": u.email,
            "rol": u.rol.value if u.rol else "sin_rol",
            "nombre": "Sin nombre",
            "extra": "",
            "puntuacion_num": 0.0  # Los clientes se quedan en 0.0
        }
        
        # Lógica para TALLERES (Con calificación)
        if u.tipo_perfil == "taller":
            taller = db.query(user_models.Taller).filter(user_models.Taller.id == u.id).first()
            if taller:
                data["nombre"] = taller.nombre_taller
                promedio = db.query(func.avg(user_models.CalificacionTaller.puntuacion))\
                             .filter(user_models.CalificacionTaller.taller_id == u.id).scalar()
                
                if promedio:
                    data["puntuacion_num"] = float(promedio)
                    data["extra"] = f"⭐ {round(promedio, 1)}/5.0"
                else:
                    data["extra"] = "⭐ Sin calificar"
        
        # Lógica para CLIENTES (Sin calificación, solo teléfono)
        elif u.tipo_perfil == "cliente":
            cliente = db.query(user_models.Cliente).filter(user_models.Cliente.id == u.id).first()
            if cliente:
                data["nombre"] = cliente.nombre
                data["extra"] = f"📱 {cliente.telefono}"
        
        resultado.append(data)

    # 3. Aplicar Ordenamiento
    if orden == "mejor_calificados":
        # Los talleres con más estrellas arriba. Los clientes y talleres sin estrellas abajo.
        resultado.sort(key=lambda x: x["puntuacion_num"], reverse=True)
    elif orden == "peor_calificados":
        # Solo tiene sentido si filtramos por talleres primero
        # Filtramos los que tienen 0 para no poner a los clientes arriba
        resultado.sort(key=lambda x: x["puntuacion_num"] if x["puntuacion_num"] > 0 else 9.9)

    return resultado


async def procesar_audio_filtros(file):
    # 1. AUDIO A TEXTO (Usando Whisper de Groq)
    audio_content = await file.read()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Petición a Whisper
        files = {'file': (file.filename, audio_content, file.content_type)}
        data = {'model': 'whisper-large-v3'}
        
        resp_audio = await client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            files=files,
            data=data
        )
        resp_audio.raise_for_status()
        texto_transcrito = resp_audio.json().get("text", "")
        
        # 2. TEXTO A FILTROS (Usando LLaMA 3.1 de Groq)
        # 2. TEXTO A FILTROS Y ACCIÓN (Usando LLaMA 3.1 de Groq)
        prompt_sistema = """
        Eres un asistente que extrae filtros y acciones para una tabla de usuarios. El usuario te dará una orden por voz.
        Devuelve ÚNICAMENTE un JSON válido con esta estructura:
        {
            "rol": "puede ser 'ADMIN_TALLER', 'CLIENTE', o '' si quiere ver todos",
            "orden": "puede ser 'mejor_calificados', 'peor_calificados' o ''",
            "accion": "puede ser 'pdf' (si pide descargar/exportar en pdf), 'excel' (si pide en excel), o 'ver' (por defecto si solo quiere mostrar en pantalla)"
        }
        Ejemplos:
        - "Quiero ver los talleres mejor calificados" -> {"rol": "ADMIN_TALLER", "orden": "mejor_calificados", "accion": "ver"}
        - "Descarga un pdf de todos los clientes" -> {"rol": "CLIENTE", "orden": "", "accion": "pdf"}
        - "Expórtame en excel los talleres con peores estrellas" -> {"rol": "ADMIN_TALLER", "orden": "peor_calificados", "accion": "excel"}
        """
        
        resp_llm = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": texto_transcrito}
                ],
                "response_format": {"type": "json_object"}, # Fuerza a devolver JSON
                "temperature": 0.1
            }
        )
        resp_llm.raise_for_status()
        respuesta_json = resp_llm.json()['choices'][0]['message']['content']
        print(respuesta_json)
        return json.loads(respuesta_json)