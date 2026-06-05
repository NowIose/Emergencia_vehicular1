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

async def analizar_emergencia_con_ia(descripcion: str, fotos_urls: List[str] | None) -> Tuple[str, str, str]:
    if not descripcion and not fotos_urls:
        return "Sin datos suficientes para analizar.", "media", "Mecánica General"

    prompt_sistema = """
    Eres un mecánico experto evaluando reportes de emergencias vehiculares. 
    Analiza la descripción del conductor y la imagen (si la hay).
    
    Debes responder ESTRICTAMENTE en este formato de 3 líneas:
    LINEA 1: Un 'Diagnóstico Preliminar' técnico y breve (máx 150 caracteres).
    LINEA 2: Clasifica la prioridad estrictamente como: 'media', 'alta' o 'baja'.
    LINEA 3: Clasifica la especialidad necesaria eligiendo UNA de estas: 'Mecánica General', 'Electricidad', 'Gomería', 'Chapa y Pintura', 'Aire Acondicionado'.
    
    Ejemplo de respuesta:
    El vehículo presenta un sobrecalentamiento en el motor posiblemente por fuga de refrigerante.
    alta
    Mecánica General
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
        # 3. EXTRAER DATOS DE LA RESPUESTA
        # ==========================================
        lineas = [l.strip() for l in respuesta_ia.strip().split("\n") if l.strip()]
        
        diagnostico = lineas[0] if len(lineas) > 0 else "Diagnóstico no disponible."
        prioridad_calculada = "media"
        especialidad_detectada = "Mecánica General"

        if len(lineas) >= 2:
            prio = lineas[1].lower()
            if "alta" in prio: prioridad_calculada = "alta"
            elif "baja" in prio: prioridad_calculada = "baja"
        
        if len(lineas) >= 3:
            especialidades_validas = ['Mecánica General', 'Electricidad', 'Gomería', 'Chapa y Pintura', 'Aire Acondicionado']
            for esp in especialidades_validas:
                if esp.lower() in lineas[2].lower():
                    especialidad_detectada = esp
                    break

        print("-" * 50)
        print(f"✅ ANÁLISIS COMPLETADO")
        print(f"Diagnóstico: {diagnostico}")
        print(f"Prioridad: {prioridad_calculada}")
        print(f"Especialidad: {especialidad_detectada}")
        print("-" * 50)
        
        return diagnostico, prioridad_calculada, especialidad_detectada

    except Exception as e:
        print(f"❌ Error al conectar con la IA: {e}")
        return "Análisis de IA temporalmente no disponible.", "media", "Mecánica General"


