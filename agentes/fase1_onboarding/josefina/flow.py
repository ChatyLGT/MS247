import re
from core import db
from core.gemini_multimodal import procesar_texto_puro
from core.grabadora import log_bot_response, log_forense, log_terminal
from agentes.fase1_onboarding.josefina import josefina # Import corregido

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core import auditor

async def manejar_josefina(update, context, telegram_id, texto, file_path=None):
    target = update.message if update.message else update.callback_query.message
    adn = db.obtener_adn_completo(telegram_id) or {}
    
    historial = adn.get('historial_reciente') or []
    hilo_txt = "\n".join([f"{m['rol']}: {m['txt']}" for m in historial[-10:]]) if historial else "Sin historial aún."
    
    prompt = f"{josefina.obtener_prompt(telegram_id)}\n\nHISTORIAL RECIENTE:\n{hilo_txt}"
    
    res_ia = await procesar_texto_puro(prompt, texto, telegram_id=telegram_id)
    
    if res_ia.startswith("⚠️ [SISTEMA]"):
        return False

    db.guardar_memoria_hilo(telegram_id, "SOCIO", texto)

    log_forense("JOSEFINA", res_ia, telegram_id)
    print(f"\n--- 🕵️ FORENSE JOSEFINA RAW ---\n{res_ia}\n-----------------------------\n")
    auditor.registrar_evento(telegram_id, "CEREBRO_IA_JOSEFINA", res_ia)

    estado_aprobado = False
    if 'ESTADO_JOSEFINA="Aprobado"' in res_ia:
        estado_aprobado = True

    res_limpia = re.sub(r'ESTADO_JOSEFINA=".*?"', '', res_ia).strip()
    res_limpia = re.sub(r'```json.*?```', '', res_limpia, flags=re.DOTALL).strip()

    db.guardar_memoria_hilo(telegram_id, "JOSEFINA", res_limpia)
    log_bot_response("JOSEFINA", res_limpia, telegram_id)

    if estado_aprobado:
        teclado = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Avanzar con Fausto", callback_data="josefina_avanzar_fausto")]
        ])
        await target.reply_text(f"✨ <b>Josefina:</b> {res_limpia}", reply_markup=teclado, parse_mode="HTML")
    else:
        await target.reply_text(f"✨ <b>Josefina:</b> {res_limpia}", parse_mode="HTML")
