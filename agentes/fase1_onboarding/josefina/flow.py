import re
from core import db
from core.gemini_multimodal import procesar_texto_puro
from core.grabadora import log_bot_response, log_forense, log_terminal
from agentes.fase1_onboarding.josefina import josefina

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core import auditor

async def manejar_josefina(update, context, telegram_id, texto, file_path=None, tools=None):
    target = update.message if update.message else update.callback_query.message
    
    try:
        with open("agentes/fase1_onboarding/josefina/SOUL.md", "r", encoding="utf-8") as f:
            soul = f.read()
    except Exception as e:
        soul = "Eres Josefina, experta en cultura e identidad."

    # Doctrina 2026: Prompt ligero + Tools
    prompt = f"{soul}\n\nREGLA 2026: Usa 'obtener_historial' si necesitas recordar la charla previa."
    
    res_ia = await procesar_texto_puro(prompt, texto, modo_json=True, telegram_id=telegram_id, tools=tools)
    
    if res_ia.startswith("⚠️ [SISTEMA]"):
        return False

    db.guardar_memoria_hilo(telegram_id, "SOCIO", texto)

    log_forense("JOSEFINA", res_ia, telegram_id)
    auditor.registrar_evento(telegram_id, "CEREBRO_IA_JOSEFINA", res_ia)

    try:
        import json
        data = json.loads(res_ia)
        mensaje = data.get("mensaje", "Interesante elección cultural.")
        bautismo_ok = data.get("bautismo_completado", False)
        nuevo_estado = data.get("intentar_cambiar_estado", "JOSEFINA_ACTIVA")
        equipo = data.get("equipo_completo", [])
        
        db.guardar_memoria_hilo(telegram_id, "JOSEFINA", mensaje)
        
        # Guardar equipo si viene en el JSON (aunque no esté completado el bautismo, para persistir nombres propuestos)
        if equipo:
            db.limpiar_equipo_usuario(telegram_id)
            for agente in equipo:
                db.agregar_agente_equipo(
                    telegram_id,
                    rol_socket=agente.get("rol"),
                    nivel="Maker", 
                    nombre=agente.get("nombre_agente", agente.get("rol")),
                    personalidad=agente.get("personalidad"),
                    estilo_narrativo=agente.get("estilo_narrativo"),
                    estilo_liderazgo=agente.get("estilo_liderazgo")
                )

        if bautismo_ok and nuevo_estado == "BRUNO_ACTIVO":
            db.actualizar_campo_usuario(telegram_id, "estado_onboarding", "BRUNO_ACTIVO")
            log_terminal(f"✅ Bautismo completado para Socio {telegram_id}. Transición a Bruno.")

        await target.reply_text(f"✨ <b>Josefina:</b> {mensaje}", parse_mode="HTML")
    except Exception as e:
        db.guardar_memoria_hilo(telegram_id, "JOSEFINA", res_ia)
        await target.reply_text(f"✨ <b>Josefina:</b> {res_ia}", parse_mode="HTML")
    return True
