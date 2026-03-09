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
    
    # Ensamblaje de contexto para Pepe
    ctx_negocio = f"""
Socio: {adn.get('nombre_completo', '')}
Empresa: {adn.get('nombre_empresa', '')}
BÓVEDA ACTUAL (Resumen acumulado): {memoria_largo_plazo}
"""
    
    cerebro_modular = compilar_cerebro_pepe()
    
    # REGLAS DINÁMICAS PARA PEPE (Inyectadas en caliente)
    reglas_extra = """
### REGLAS DE FLUJO CRÍTICAS ###
1. **SECUENCIALIDAD**: USA EL CUESTIONARIO_150 NIVEL POR NIVEL. No saltes bloques. Empieza por Nivel 1 A, luego B, C.
2. **TONO Y EMPATÍA**: Si el usuario responde corto, está apurado o pide avanzar, CIERRA EL NIVEL ACTUAL y ofrece pasar a María. No seas "a lo bruto".
3. **RESUMEN**: Mantén el objeto "RESUMEN_ACUMULADO" actualizado con los datos técnicos que vayas descubriendo.
"""
    
    prompt = f"{cerebro_modular}\n{reglas_extra}\n{ctx_negocio}\nHISTORIAL RECIENTE:\n{hilo_txt}"
    
    # Procesamos la IA directamente porque Jero ya mandó la UX de espera
    res_ia = await procesar_texto_puro(prompt, texto, telegram_id=telegram_id)
    
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
