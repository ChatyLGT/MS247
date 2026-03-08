import os
import re, asyncio
from core import db
from core import auditor, obsidian
from core.gemini_multimodal import procesar_texto_puro
from core.logger_omnisciente import obtener_chismografo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

log = obtener_chismografo("PEPE_FLOW")

def compilar_cerebro_pepe():
    base_path = "agentes/fase1_onboarding/pepe"
    alma_compilada = ""
    modulos = ["identity.md", "voice.md", "playbook.md"]
    for modulo in modulos:
        path = os.path.join(base_path, modulo)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                alma_compilada += f"\n\n### MODULO: {modulo.upper()} ###\n{f.read()}"
    
    # Inyectar las 150 preguntas como anexo
    path_cuestionario = "knowledge_base/cuestionario_pepe_150.md"
    if os.path.exists(path_cuestionario):
        with open(path_cuestionario, "r", encoding="utf-8") as f:
             alma_compilada += f"\n\n### MODULO: CUESTIONARIO_150 ###\n{f.read()}"
             
    return alma_compilada

async def manejar_pepe(update, context, telegram_id, texto, file_path=None):
    target = update.message if update.message else update.callback_query.message
    adn = db.obtener_adn_completo(telegram_id) or {}
    
    historial = adn.get('historial_reciente') or []
    hilo_txt = "\n".join([f"{m['rol']}: {m['txt']}" for m in historial[-6:]]) if historial else "Sin historial aún."
    
    memoria_largo_plazo = obsidian.leer_documento(telegram_id, "02_diagnostico_pepe.md")
    ctx_negocio = f"BÓVEDA ACTUAL: Socio {adn.get('nombre_completo', '')} | Negocio {adn.get('nombre_empresa', '')}\nMEMORIA LARGO PLAZO: {memoria_largo_plazo}"
    
    cerebro_modular = compilar_cerebro_pepe()
    prompt = f"{cerebro_modular}\n\n{ctx_negocio}\n\nHISTORIAL RECIENTE:\n{hilo_txt}"
    
    # Procesamos la IA directamente porque Jero ya mandó la UX de espera
    res_ia = await procesar_texto_puro(prompt, texto, telegram_id=telegram_id)
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
