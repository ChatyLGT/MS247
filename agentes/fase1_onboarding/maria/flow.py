import re
from core import db
import asyncio
from core import auditor
from core.gemini_multimodal import procesar_texto_puro
from core.grabadora import log_bot_response, log_forense, log_terminal
from agentes.fase1_onboarding.maria import maria # Import corregido

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def manejar_maria(update, context, telegram_id, texto, file_path=None, tools=None):
    target = update.message if update.message else update.callback_query.message
    
    try:
        with open("agentes/fase1_onboarding/maria/SOUL.md", "r", encoding="utf-8") as f:
            soul = f.read()
    except Exception as e:
        soul = "Eres María, la arquitecta de la mesa directiva."

    # Doctrina 2026: Prompt ligero + Tools
    prompt = f"{soul}\n\nREGLAS 2026:\n1. Usa 'obtener_historial' si necesitas contexto previo.\n2. Usa 'leer_boveda' para el diagnóstico de Pepe."
    
    # Obtener ADN para contexto ligero si es necesario (Opcional, preferible dejar que ella lo pida)
    
    res_ia = await procesar_texto_puro(prompt, texto, telegram_id=telegram_id, tools=tools)
    
    if res_ia.startswith("⚠️ [SISTEMA]"):
        log_forense("MARIA_ERROR", res_ia, telegram_id)
        return False # Indicar falla al orquestador

    db.guardar_memoria_hilo(telegram_id, "SOCIO", texto)

    auditor.registrar_evento(telegram_id, "CEREBRO_IA_MARIA", res_ia)
    log_forense("MARIA", res_ia, telegram_id)
    print(f"\n--- 🕵️ FORENSE MARIA RAW ---\n{res_ia}\n-----------------------------\n")

    # 1. Buscamos el semáforo para avanzar
    estado_aprobado = False
    if 'ESTADO_MARIA="Aprobado"' in res_ia:
        estado_aprobado = True

    # 2. Limpieza de pantalla (escondemos la etiqueta y los posibles JSON de la vista del usuario)
    res_limpia = re.sub(r'ESTADO_MARIA=".*?"', '', res_ia).strip()
    res_limpia = re.sub(r'```json.*?```', '', res_limpia, flags=re.DOTALL).strip()

    db.guardar_memoria_hilo(telegram_id, "MARIA", res_limpia)
    log_bot_response("MARIA", res_limpia, telegram_id)

    # 3. La claqueta de acción
    if estado_aprobado:
        teclado = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Avanzar con Josefina", callback_data="maria_avanzar_josefina")]
        ])
        await target.reply_text(f"<b>María:</b> {res_limpia}", reply_markup=teclado, parse_mode="HTML")
    else:
        await target.reply_text(f"<b>María:</b> {res_limpia}", parse_mode="HTML")
    
    return True
