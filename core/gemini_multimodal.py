import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def obtener_mime_type(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    mapping = {
        ".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp", ".oga": "audio/ogg",
        ".ogg": "audio/ogg", ".wav": "audio/wav", ".mp3": "audio/mpeg"
    }
    return mapping.get(ext, "application/octet-stream")

async def describir_contenido_multimodal(file_path):
    if not file_path or not os.path.exists(file_path): return ""
    mime = obtener_mime_type(file_path)
    with open(file_path, "rb") as f: file_bytes = f.read()

    try:
        prompt = "Si es audio, transcribe TODO exactamente. Si es PDF/Imagen, describe el contenido clave detalladamente."
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Part.from_bytes(data=file_bytes, mime_type=mime), prompt]
        )
        return response.text.strip()
    except Exception as e:
        return f"Error en percepción: {e}"

import asyncio
from core import db

async def procesar_multimodal(file_path, prompt_agente):
    descripcion = await describir_contenido_multimodal(file_path)
    prompt_final = f"{prompt_agente}\n\nCONTENIDO DEL ARCHIVO RECIBIDO: {descripcion}"
    texto, tokens = await procesar_texto_puro(prompt_final, "[Archivo Adjunto]")
    return texto, descripcion

async def procesar_texto_puro(prompt_sistema, texto_usuario, modo_json=False, telegram_id=None, tools=None):
    try:
        kwargs = {}
        if modo_json:
            kwargs["response_mime_type"] = "application/json"
        if tools:
            kwargs["tools"] = tools
            
        config = types.GenerateContentConfig(**kwargs) if kwargs else None
            
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"{prompt_sistema}\n\nUsuario: {texto_usuario}\nREGLA: Máximo 1500 caracteres.",
            config=config
        )
        
        # Telemetría
        if response.usage_metadata and telegram_id:
            tokens = response.usage_metadata.total_token_count
            # Fire and forget
            asyncio.create_task(asyncio.to_thread(db.restar_tokens_gasolina, telegram_id, tokens))
                
        return response.text
    except Exception as e:
        print(f"🔥 ERROR GEMINI CRÍTICO: {e}")
        return "Error en mis neuronas."
