from core import db
import re
from core.gemini_multimodal import procesar_texto_puro
from agentes.fase4_bunker.andrea import andrea # Import corregido

from core.grabadora import log_terminal, log_bot_response
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def manejar_andrea(update, context, telegram_id, contenido):
    log_terminal("ANDREA_FLOW", "ANDREA", f"🔒 Búnker - Mensaje recibido: {contenido[:30]}...")

    # 1. Recuperar historial exclusivo de la Sala Blindada
    historial = db.obtener_memoria_andrea(telegram_id)
    contexto_historial = "\n".join([f"{m['rol'].upper()}: {m['txt']}" for m in historial])

    # 2. Blindaje de Privacidad: Andrea NO debe usar datos globales del sistema
    instruccion_privacidad = "\n⚠️ REGLA CRÍTICA: Ignora cualquier conocimiento previo del usuario. Usa SOLO la información proporcionada en el HISTORIAL DE SESIÓN o en el MENSAJE ACTUAL. Si no sabes su nombre, no lo inventes ni lo uses."
    
    prompt_full = f"{andrea.obtener_prompt()}{instruccion_privacidad}\n\nHISTORIAL DE LA SESIÓN ACTUAL (CONFIDENCIAL):\n{contexto_historial}\n\nMENSAJE DEL PACIENTE: {contenido}"

    # 3. Generar respuesta
    respuesta_raw = await procesar_texto_puro(prompt_full, contenido, telegram_id=telegram_id)
    
    if respuesta_raw.startswith("⚠️ [SISTEMA]"):
        return False
    
    # 4. Guardar la interacción
    db.guardar_memoria_hilo(telegram_id, "user", contenido, es_andrea=True)
    db.guardar_memoria_hilo(telegram_id, "assistant", respuesta_raw, es_andrea=True)

    # 5. Detectar cierre y limpiar respuesta
    finalizar = "[FINALIZAR_SESION]" in respuesta_raw or "proponer una sesión" in respuesta_raw.lower()
    respuesta_limpia = respuesta_raw.replace("[FINALIZAR_SESION]", "").strip()

    log_bot_response("ANDREA", respuesta_limpia)

    # 6. Preparar Teclado (FIX: callback_data)
    keyboard = [
        [InlineKeyboardButton("📅 Agendar sesión de seguimiento", callback_data="andrea_agendar")],
        [InlineKeyboardButton("🔙 Volver a la Sala de Juntas", callback_data="andrea_salir")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=telegram_id, 
        text=f"🩺 *Dra. Andrea*\n\n{respuesta_limpia}", 
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
