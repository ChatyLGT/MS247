import os, json, logging
from core import db
from core.ui import obtener_teclado_por_estado
from core.gemini_multimodal import procesar_texto_puro

logger = logging.getLogger("SOFY_FLOW")

async def manejar_onboarding(update, context, telegram_id, estado, texto_usuario, tools=None):
    try:
        with open("agentes/fase1_onboarding/sofy/SOUL.md", "r", encoding="utf-8") as f: soul = f.read()
    except: soul = "Eres Sofy, la hostess de onboarding."

    u = db.obtener_adn_completo(telegram_id)
    memoria_mini = {"nombre": u.get("nombre_completo", "N/A"), "empresa": u.get("nombre_empresa", "N/A")}
    prompt_sistema = f"{soul}\n\nMEMORIA ACTUAL:\n{memoria_mini}\nESTADO ACTUAL: {estado}"
    
    res_ia = await procesar_texto_puro(prompt_sistema, texto_usuario, modo_json=True, telegram_id=telegram_id, tools=tools)
    
    if res_ia and res_ia.startswith("⚠️ [SISTEMA]"):
        await update.effective_message.reply_text("💼 <b>Jero:</b> Sofy tiene un contratiempo técnico.", parse_mode="HTML")
        return

    logger.info(f"[SOFY_LOG] RAW IA: {res_ia}")
    
    try:
        data = json.loads(res_ia)
        mensaje = data.get("mensaje", "Continuemos.")
        
        if data.get("nombre_detectado"): db.actualizar_campo_usuario(telegram_id, "nombre_completo", data["nombre_detectado"])
        if data.get("empresa_detectada"): db.actualizar_adn(telegram_id, "nombre_empresa", data["empresa_detectada"])

        if estado == "SOFY_ACTIVA":
            from core.pdf_generator import generar_pdf_dossier
            logger.info(f"[SOFY] Fase de Cierre para {telegram_id}.")
            pdf_path = generar_pdf_dossier(telegram_id)
            await update.effective_message.reply_text(f"✨ <b>Sofy:</b> {mensaje}", parse_mode="HTML")
            with open(pdf_path, 'rb') as f:
                await context.bot.send_document(chat_id=telegram_id, document=f, caption="Sofy: Tu Dossier está listo.", parse_mode="HTML")
            db.actualizar_campo_usuario(telegram_id, "estado_onboarding", "KICKOFF")
            return

        intentar_estado = data.get("intentar_cambiar_estado")
        nuevo_estado = intentar_estado if intentar_estado else estado
        if nuevo_estado != estado:
            db.actualizar_campo_usuario(telegram_id, "estado_onboarding", nuevo_estado)

        reply_markup = obtener_teclado_por_estado(nuevo_estado)
        await update.effective_message.reply_text(f"<b>Sofy:</b> {mensaje}", reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Falla Sofy: {e}")
        await update.effective_message.reply_text("Sofy: ⚠️ Protocolo interferido.")
