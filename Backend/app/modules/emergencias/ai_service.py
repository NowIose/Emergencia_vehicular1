import httpx
import os
from typing import List, Tuple
from dotenv import load_dotenv

# Nuevo SDK de Google
from google import genai
from google.genai import types

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Modelo de Visión oficial confirmado
MODELO_GEMINI = "gemini-2.5-flash"

async def analizar_emergencia_con_ia(descripcion: str, fotos_urls: List[str] | None) -> Tuple[str, str]:
    if not descripcion and not fotos_urls:
        return "Sin datos suficientes para analizar.", "media"

    prompt_sistema = """
    Eres un mecánico experto evaluando reportes de emergencias vehiculares. 
    Analiza la descripción del conductor y la imagen (si la hay).
    1. Redacta un 'Diagnóstico Preliminar' técnico y muy breve para el taller. NO uses emojis no exageres con el diagnóstico.
    2. Al final, clasifica la prioridad estrictamente como: 'media', 'alta' o 'baja'.
    """

    try:
        respuesta_ia = ""

        # ==========================================
        # CASO 1: TIENE FOTOS -> Usamos GEMINI 2.5 FLASH
        # ==========================================
        if fotos_urls and len(fotos_urls) > 0:
            print(f"📸 Foto detectada: Analizando con Gemini ({MODELO_GEMINI})...")
            
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            async with httpx.AsyncClient(timeout=30.0) as client_http:
                # Descargamos la primera foto de Cloudinary
                resp = await client_http.get(fotos_urls[0])
                if resp.status_code == 200:
                    imagen_part = types.Part.from_bytes(
                        data=resp.content,
                        mime_type='image/jpeg'
                    )
                    
                    prompt_usuario = f"{prompt_sistema}\n\nDescripción del cliente: {descripcion}"
                    
                    # Llamada asíncrona a Gemini
                    response = await client.aio.models.generate_content(
                        model=MODELO_GEMINI,
                        contents=[prompt_usuario, imagen_part]
                    )
                    respuesta_ia = response.text
                else:
                    raise Exception(f"Error descargando imagen de Cloudinary: {resp.status_code}")

        # ==========================================
        # CASO 2: SOLO TEXTO -> Usamos GROQ (LLaMA 3.1)
        # ==========================================
        else:
            print("📝 Solo texto detectado: Analizando con LLaMA 3.1 (Groq)...")
            
            async with httpx.AsyncClient(timeout=15.0) as client_http:
                response = await client_http.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [
                            {"role": "system", "content": prompt_sistema},
                            {"role": "user", "content": f"Descripción del cliente: {descripcion}"}
                        ],
                        "max_tokens": 300,
                        "temperature": 0.3
                    }
                )
                response.raise_for_status()
                data = response.json()
                respuesta_ia = data['choices'][0]['message']['content']

        # ==========================================
        # 3. EXTRAER LA PRIORIDAD DEL TEXTO
        # ==========================================
        respuesta_ia_limpia = respuesta_ia.lower().replace("*", "")
        prioridad_calculada = "media" # Por defecto
        
        if "prioridad: alta" in respuesta_ia_limpia or "prioridad alta" in respuesta_ia_limpia:
            prioridad_calculada = "alta"
        elif "prioridad: baja" in respuesta_ia_limpia or "prioridad baja" in respuesta_ia_limpia:
            prioridad_calculada = "baja"

        print("-" * 50)
        print(f"✅ ANÁLISIS COMPLETADO (Prioridad IA: {prioridad_calculada})")
        print(respuesta_ia)
        print("-" * 50)
        
        return respuesta_ia, prioridad_calculada

    except Exception as e:
        print(f"❌ Error al conectar con la IA: {e}")
        return "Análisis de IA temporalmente no disponible.", "media"


