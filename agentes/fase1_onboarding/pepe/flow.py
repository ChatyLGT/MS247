import os
import re, asyncio
from core import db
from core import auditor, obsidian
from core.gemini_multimodal import procesar_texto_puro
from core.logger_omnisciente import obtener_chismografo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

log = obtener_chismografo("PEPE_FLOW")

async def manejar_pepe(update, context, telegram_id, texto, file_path=None, tools=None):
    target = update.message if update.message else update.callback_query.message
    
    try:
        with open("agentes/fase1_onboarding/pepe/SOUL.md", "r", encoding="utf-8") as f:
            soul = f.read()
    except Exception as e:
        soul = "Eres Pepe, consultor de negocios."

    prompt_base = f"{soul}\n\nRECUERDA: Mantén el diagnóstico actualizado en la bóveda."
    
    # Procesamos con Tools
    res_ia = await procesar_texto_puro(prompt_base, texto, telegram_id=telegram_id, tools=tools)
    
    if res_ia.startswith("⚠️ [SISTEMA]"):
        log.error(f"Pepe falló por error de sistema: {res_ia}")
        return False # Falla para el orquestador

    db.guardar_memoria_hilo(telegram_id, "SOCIO", texto)

    m_resumen = re.search(r'RESUMEN_ACUMULADO:\s*["\']?(.*?)["\']?(?=\n|$)', res_ia, re.IGNORECASE | re.DOTALL)
    if m_resumen:
        obsidian.guardar_documento(telegram_id, "02_diagnostico_pepe.md", m_resumen.group(1).strip())

    checklist_completo = False
    m_check = re.search(r'ESTADO_CHECKLIST:\s*rubro=[\'"]?([^\'"\n]+)[\'"]?\s*dolor=[\'"]?([^\'"\n]+)[\'"]?\s*modelo=[\'"]?([^\'"\n]+)[\'"]?', res_ia, re.IGNORECASE)
    if m_check:
        cr, cd, cm = m_check.groups()
        if cr.strip().lower() == "ok" and cd.strip().lower() == "ok" and cm.strip().lower() == "ok":
            checklist_completo = True

    # 3. Limpieza de pantalla (Eliminar el JSON interno aunque la IA no ponga los guiones '---')
    res_limpia = re.sub(r'(?i)(ESTADO_CHECKLIST|RESUMEN_ACUMULADO).*', '', res_ia, flags=re.DOTALL).strip()
    res_limpia = re.sub(r'-{3,}', '', res_limpia).strip()
    
    db.guardar_memoria_hilo(telegram_id, "PEPE", res_limpia)

    if checklist_completo:
        teclado = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Faltan detalles", callback_data="pepe_mas_contexto")],
            [InlineKeyboardButton("🚀 Todo claro, avanzar con María", callback_data="pepe_avanzar_maria")]
        ])
        await target.reply_text(f"<b>Pepe:</b> {res_limpia}\n\n<i>(Sistema: Pepe ha completado el perfil base)</i>", reply_markup=teclado, parse_mode="HTML")
    else:
        await target.reply_text(f"<b>Pepe:</b> {res_limpia}", parse_mode="HTML")
