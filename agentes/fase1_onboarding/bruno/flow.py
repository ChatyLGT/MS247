import json
import logging
from core import db
from core.gemini_multimodal import procesar_texto_puro
from core.grabadora import log_terminal

logger = logging.getLogger("BRUNO_FLOW")

async def manejar_bruno(update, context, telegram_id, texto, tools=None):
    target = update.message if update.message else update.callback_query.message
    
    try:
        with open("agentes/fase1_onboarding/bruno/SOUL.md", "r", encoding="utf-8") as f:
            soul = f.read()
            
        with open("agentes/fase1_onboarding/bruno/playbook_estructural.md", "r", encoding="utf-8") as f:
            playbook = f.read()
    except Exception as e:
        soul = "Eres Bruno, el director del Programa de Inteligencia Estructural."
        playbook = "Fase 1: Claridad Estructural."

    # ADN Dinámico para Bruno
    adn = db.obtener_adn_completo(telegram_id)
    rubro = adn.get("rubro", "tu negocio")
    dolor = adn.get("dolor_principal", "los problemas de gestión")
    personalidad = adn.get("personalidad_agentes", "estructurado")
    dias_previos = adn.get("dias_compromiso", [])
    hora_inicio_previa = adn.get("hora_inicio", "")
    duracion_previa = adn.get("duracion_minutos", 0)
    
    prompt = f"{soul}\n\nPLAYBOOK ESTRUCTURAL:\n{playbook}\n\nCONTEXTO DINÁMICO DEL SOCIO:\nRubro: {rubro}\nDolor: {dolor}\nPersonalidad Exigida: {personalidad}\n"
    prompt += f"Días de compromiso YA pactados anteriormente: {dias_previos}\nHora de inicio YA pactada: {hora_inicio_previa}\nDuración YA pactada: {duracion_previa} mins\n\n"
    prompt += "REGLA 2026: Interpreta el contexto y exige el Pacto de Sangre completo (días del mes, hora de inicio exacta en 24h, y duración en minutos). Si el usuario ya dio los datos en turnos previos, inclúyelos en tu JSON de respuesta y NO los olvides. Genera un plan accionario leyendo SOLO la Fase 1 del Playbook adaptado al rubro solo si ya tienes días, hora inicial y duración completos."
    
    res_ia = await procesar_texto_puro(prompt, texto, modo_json=True, telegram_id=telegram_id, tools=tools)
    
    if res_ia.startswith("⚠️ [SISTEMA]"):
        logger.error(f"Bruno falló: {res_ia}")
        return False
        
    db.guardar_memoria_hilo(telegram_id, "SOCIO", texto)
    logger.info(f"🧠 [BRUNO_LOG] RAW IA: {res_ia}")
    
    try:
        data = json.loads(res_ia)
        mensaje = data.get("mensaje", "Vamos a estructurar este proyecto.")
        dias = data.get("dias_compromiso", [])
        hora_inicio = data.get("hora_inicio", "")
        duracion = data.get("duracion_minutos", 0)
        plan = data.get("plan_accion", [])
        nuevo_estado = data.get("intentar_cambiar_estado", "BRUNO_ACTIVO")
        
        # Extracción de ADN en vivo por Bruno
        nuevo_rubro = data.get("rubro")
        nuevo_dolor = data.get("dolor")
        if nuevo_rubro: db.actualizar_adn(telegram_id, "rubro", nuevo_rubro)
        if nuevo_dolor: db.actualizar_adn(telegram_id, "dolor_principal", nuevo_dolor)
        
        db.guardar_memoria_hilo(telegram_id, "BRUNO", mensaje)
        
        # Save partial pact state to prevent amnesia
        if dias: db.actualizar_adn(telegram_id, "dias_compromiso", dias)
        if hora_inicio: db.actualizar_adn(telegram_id, "hora_inicio", hora_inicio)
        if duracion: db.actualizar_adn(telegram_id, "duracion_minutos", duracion)
        
        if nuevo_estado == "OPERACION_CONTINUA":
            # Pacto cerrado, guardar el estructurado final.
            pacto = {
                "dias": dias,
                "hora_inicio": hora_inicio,
                "duracion_minutos": duracion,
                "plan_accion": plan
            }
            db.actualizar_adn(telegram_id, "pacto_bruno", pacto)
            # VERA-026: Transición a Sofy para el Cierre y PDF
            db.actualizar_campo_usuario(telegram_id, "estado_onboarding", "SOFY_ACTIVA")
            log_terminal(f"📋 Bruno cerró el pacto para {telegram_id}. Pasando a Sofy para el Dossier.")
            
        await target.reply_text(f"📋 <b>Bruno:</b> {mensaje}", parse_mode="HTML")
        return True
    except Exception as e:
        logger.error(f"Error parseando JSON de Bruno: {e}")
        db.guardar_memoria_hilo(telegram_id, "BRUNO", res_ia)
        await target.reply_text(f"📋 <b>Bruno:</b> {res_ia}", parse_mode="HTML")
        return True
