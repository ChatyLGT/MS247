import re
from core import db
from core.gemini_multimodal import procesar_texto_puro
from core.grabadora import log_bot_response, log_forense, log_terminal
from agentes.fase2_directorio.fausto import fausto # Import corregido

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core import auditor

async def manejar_fausto(update, context, telegram_id, texto, file_path=None):
    target = update.message if update.message else update.callback_query.message
    adn = db.obtener_adn_completo(telegram_id) or {}
    
    historial = adn.get('historial_reciente') or []
    hilo_txt = "\n".join([f"{m['rol']}: {m['txt']}" for m in historial[-12:]]) if historial else "Sin historial aún."
    
    prompt = f"{fausto.obtener_prompt(telegram_id)}\n\nHISTORIAL RECIENTE:\n{hilo_txt}"
    
    res_ia = await procesar_texto_puro(prompt, texto, telegram_id=telegram_id)
    db.guardar_memoria_hilo(telegram_id, "SOCIO", texto)

    log_forense("FAUSTO", res_ia, telegram_id)
    print(f"\n--- 🕵️ FORENSE FAUSTO RAW ---\n{res_ia}\n-----------------------------\n")
    auditor.registrar_evento(telegram_id, "CEREBRO_IA_FAUSTO", res_ia)

    estado_aprobado = False
    if 'ESTADO_FAUSTO="Aprobado"' in res_ia:
        estado_aprobado = True

    res_limpia = re.sub(r'ESTADO_FAUSTO=".*?"', '', res_ia).strip()
    res_limpia = re.sub(r'```json.*?```', '', res_limpia, flags=re.DOTALL).strip()

    db.guardar_memoria_hilo(telegram_id, "FAUSTO", res_limpia)
    log_bot_response("FAUSTO", res_limpia, telegram_id)

    if estado_aprobado:
        teclado = InlineKeyboardMarkup([
            [InlineKeyboardButton("👑 Terminar y volver a Sofía", callback_data="fausto_avanzar_sofia")]
        ])
        await target.reply_text(f"⚙️ <b>Fausto:</b> {res_limpia}", reply_markup=teclado, parse_mode="HTML")
    else:
        await target.reply_text(f"⚙️ <b>Fausto:</b> {res_limpia}", parse_mode="HTML")
