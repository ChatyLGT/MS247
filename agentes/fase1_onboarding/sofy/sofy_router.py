import os, json, logging
from core import db
from core.ui import obtener_teclado_por_estado
from core.gemini_multimodal import procesar_texto_puro

logger = logging.getLogger("SOFY_FLOW")

async def manejar_onboarding(update, context, telegram_id, estado, texto_usuario):
    try:
        with open("knowledge_base/manual_ms247.txt", "r") as f:
            manual = f.read()
        with open("agentes/fase1_onboarding/sofy/playbook.md", "r") as f:
            playbook = f.read()
    except Exception as e:
        logger.error(f"Error doctrina: {e}")
        return

    # Legajo ADN Completo
    u = db.obtener_adn_completo(telegram_id)
    memoria = {
        "nombre": u.get("nombre_completo", "N/A"),
        "email": u.get("email", "N/A"),
        "empresa": u.get("nombre_empresa", "N/A")
    }

    prompt_sistema = f"{playbook}\n\nMANUAL:\n{manual}\n\nMEMORIA ACTUAL:\n{memoria}\nESTADO ACTUAL DEL SISTEMA: {estado}"
    
    # Llamada con Modo JSON
    res_ia = await procesar_texto_puro(prompt_sistema, texto_usuario, modo_json=True, telegram_id=telegram_id)
    
    if res_ia.startswith("⚠️ [SISTEMA]"):
        logger.error(f"Sofy falló por error de sistema: {res_ia}")
        await update.effective_message.reply_text("💼 <b>Jero (CEO):</b> Hola, soy Jero. Sofy ha tenido un contratiempo técnico en la entrada. Por favor, intenta enviarme el mensaje de nuevo en unos segundos mientras estabilizamos el sistema.", parse_mode="HTML")
        return

    # LOG DE INTELIGENCIA (Para auditoría)
    logger.info(f"🧠 [SOFY_LOG] RAW IA: {res_ia}")
    
    try:
        data = json.loads(res_ia)
        mensaje = data.get("mensaje", "Continuemos con el rito.")
        
        # 1. Recolección silenciosa (Paso 15A)
        if data.get("nombre_detectado"): db.actualizar_campo_usuario(telegram_id, "nombre_completo", data["nombre_detectado"])
        if data.get("email_detectado"): db.actualizar_campo_usuario(telegram_id, "email", data["email_detectado"])
        if data.get("empresa_detectada"): db.actualizar_adn(telegram_id, "nombre_empresa", data["empresa_detectada"])

        # 2. Control de Estado
        nuevo_estado = data.get("intentar_cambiar_estado", estado)
        # Asegurarnos de que no abandone NUEVO sin el evento del botón, o si el LLM decide avanzar. 
        # Pero respetando SIEMPRE el mensaje generado dinámicamente.
        if nuevo_estado != estado:
            db.actualizar_campo_usuario(telegram_id, "estado_onboarding", nuevo_estado)

        # 3. Interfaz Modular
        reply_markup = obtener_teclado_por_estado(nuevo_estado)
        target = update.effective_message
        
        await target.reply_text(
            f"<b>Sofy:</b> {mensaje}", 
            reply_markup=reply_markup, 
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Falla procesamiento Sofy: {e}")
        await update.effective_message.reply_text("Sofy: ⚠️ Mi protocolo de portería ha sufrido una interferencia.")

