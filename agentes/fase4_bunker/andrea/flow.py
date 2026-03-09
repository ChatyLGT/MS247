from core import db
import re
from core.gemini_multimodal import procesar_texto_puro
from agentes.fase4_bunker.andrea import andrea

from core.grabadora import log_terminal, log_bot_response
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def manejar_andrea(update, context, telegram_id, contenido, tools=None):
    log_terminal("ANDREA_FLOW", "ANDREA", f"🔒 Búnker - Mensaje recibido: {contenido[:30]}...")

    try:
        with open("agentes/fase4_bunker/andrea/SOUL.md", "r", encoding="utf-8") as f:
            soul = f.read()
    except Exception as e:
        soul = "Eres la Dra. Andrea, coach de alto rendimiento."

    # Doctrina 2026: Andrea es ultra-privada, pero puede usar herramientas para su PROPIA memoria.
    prompt_full = f"{soul}\n\nREGLA CRÍTICA: Ignora conocimiento fuera de esta sala. Tu memoria es privada (usa obtener_historial)."

    # Generar respuesta con tools (por si necesita su memoria blindada)
    respuesta_raw = await procesar_texto_puro(prompt_full, contenido, telegram_id=telegram_id, tools=tools)
    
    if respuesta_raw.startswith("⚠️ [SISTEMA]"):
        return False
    
    # Guardar la interacción (es_andrea=True asegura que vaya a la tabla blindada)
    db.guardar_memoria_hilo(telegram_id, "user", contenido, es_andrea=True)
    db.guardar_memoria_hilo(telegram_id, "assistant", respuesta_raw, es_andrea=True)

    # Detectar cierre y limpiar respuesta
    finalizar = "[FINALIZAR_SESION]" in respuesta_raw or "proponer una sesión" in respuesta_raw.lower()
    respuesta_limpia = respuesta_raw.replace("[FINALIZAR_SESION]", "").strip()

    log_bot_response("ANDREA", respuesta_limpia)

    # Preparar Teclado
    keyboard = [
        [InlineKeyboardButton("📅 Agendar sesión de seguimiento", callback_data="andrea_agendar")],
        [InlineKeyboardButton("🔙 Volver a la Sala de Juntas", callback_data="andrea_salir")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=telegram_id, 
        text=f"🩺 <b>Dra. Andrea</b>\n\n{respuesta_limpia}", 
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return True
