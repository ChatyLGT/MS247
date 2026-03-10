import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

from core.logger_omnisciente import obtener_chismografo, log_evento_crudo

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
log = obtener_chismografo("GEMINI_API")

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
        log.info(f"[GEMINI VISION/AUDIO] Procesando archivo: {file_path} (MIME: {mime})")
        
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Part.from_bytes(data=file_bytes, mime_type=mime), prompt]
        )
        log_evento_crudo("GEMINI_API", f"[EXTRACCION MULTIMODAL EXITOSA]", {"transcripcion": response.text.strip()})
        return response.text.strip()
    except Exception as e:
        log.error(f"Error en percepcion multimodal: {e}")
        return f"Error en percepcion: {e}"

import asyncio
from core import db

async def procesar_multimodal(file_path, prompt_agente):
    descripcion = await describir_contenido_multimodal(file_path)
    prompt_final = f"{prompt_agente}\n\nCONTENIDO DEL ARCHIVO RECIBIDO: {descripcion}"
    texto = await procesar_texto_puro(prompt_final, "[Archivo Adjunto]")
    return texto, descripcion

async def procesar_texto_puro(prompt_sistema, texto_usuario, modo_json=False, telegram_id=None, tools=None, response_schema=None):
    try:
        kwargs = {}
        if modo_json or response_schema:
            kwargs["response_mime_type"] = "application/json"
        if response_schema:
            kwargs["response_schema"] = response_schema
        if tools:
            kwargs["tools"] = tools
            
        config = types.GenerateContentConfig(**kwargs) if kwargs else None
        log.info(f"[GEMINI PROMPT IN] MODO JSON: {modo_json} | SCHEMA: {response_schema is not None}")
        
        # Start a chat session for autonomous function calling
        chat = client.aio.chats.create(model="gemini-2.0-flash", config=config)
        
        full_prompt = f"INSTINTO/SISTEMA:\n{prompt_sistema}\n\nUSUARIO:\n{texto_usuario}\nREGLA: Maximo 1500 caracteres."
        response = await chat.send_message(full_prompt)
        
        # Telemetria de la primera llamada
        if response.usage_metadata and telegram_id:
            asyncio.create_task(asyncio.to_thread(db.restar_tokens_gasolina, telegram_id, response.usage_metadata.total_token_count))

        # Loop de Function Calling (Logica 2026)
        while response.function_calls:
            from core.tools_ms247 import handlers
            parts_out = []
            
            for fc in response.function_calls:
                name = fc.name
                args = fc.args
                log.info(f"[AUTOTools] Ejecutando: {name} con {args}")
                
                if name in handlers:
                    # Si la funcion requiere telegram_id, se lo pasamos
                    import inspect
                    sig = inspect.signature(handlers[name])
                    if "telegram_id" in sig.parameters:
                        result = handlers[name](telegram_id=telegram_id, **args)
                    else:
                        result = handlers[name](**args)
                else:
                    result = f"Error: Tool {name} no encontrada o sin handler."

                parts_out.append(types.Part.from_function_response(name=name, response={"result": result}))

            # Enviar el lote de respuestas de funciones de vuelta a Gemini
            response = await chat.send_message(parts_out)
            
            if response.usage_metadata and telegram_id:
                asyncio.create_task(asyncio.to_thread(db.restar_tokens_gasolina, telegram_id, response.usage_metadata.total_token_count))

        log_evento_crudo("GEMINI_API", "[GEMINI RESPONSE OUT]", {"respuesta_raw": response.text})
        return response.text
    except Exception as e:
        error_msg = str(e).lower()
        log.error(f"ERROR GEMINI CRITICO: {e}")
        
        if "429" in error_msg or "resource_exhausted" in error_msg:
             return "[SISTEMA]: Mis neuronas estan saturadas procesando mucha informacion ahora mismo. Por favor, dame un minuto de respiro y vuelve a intentarlo. (Error de Quota 429)"
        
        if "400" in error_msg or "invalid_argument" in error_msg:
             return "[SISTEMA]: He tenido un pequeño cortocircuito analizando este mensaje especifico. Podrias intentar decirmelo de otra forma? (Error de Contexto 400)"

        return "[SISTEMA]: He tenido una falla tecnica momentanea. Jero ya esta revisando mis circuitos... (Error General)"
