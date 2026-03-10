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
    adn = db.obtener_adn_completo(telegram_id)
    datos_conocidos = {
        "Rubro": adn.get("rubro", ""),
        "Dolor Principal": adn.get("dolor_principal", ""),
        "Modelo de Negocio": adn.get("modelo_negocio", "") # Asumiendo modelo de negocio aquí o similar
    }
    
    prompt_base = f"{soul}\n\nDATOS YA CONOCIDOS (NO VUELVAS A PREGUNTAR ESTO):\n{datos_conocidos}\n\nRECUERDA: Mantén el diagnóstico actualizado en la bóveda."
    
    # Procesamos con Tools y forzamos JSON
    res_ia = await procesar_texto_puro(prompt_base, texto, modo_json=True, telegram_id=telegram_id, tools=tools)
    
    if res_ia.startswith("⚠️ [SISTEMA]"):
        log.error(f"Pepe falló por error de sistema: {res_ia}")
        return False # Falla para el orquestador

    # LOG DE INTELIGENCIA
    log.info(f"🧠 [PEPE_LOG] RAW IA: {res_ia}")
    
    try:
        import json
        clean_res = res_ia.strip()
        if "```json" in clean_res:
            clean_res = clean_res.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_res:
            clean_res = clean_res.split("```")[1].split("```")[0].strip()
            
        data = json.loads(clean_res)
        mensaje = data.get("mensaje", "Interesante, cuéntame más.")
        
        db.guardar_memoria_hilo(telegram_id, "SOCIO", texto)
        db.guardar_memoria_hilo(telegram_id, "PEPE", mensaje)

        resumen_acumulado = data.get("resumen_acumulado")
        if resumen_acumulado:
            obsidian.guardar_documento(telegram_id, "02_diagnostico_pepe.md", resumen_acumulado)
            db.actualizar_adn(telegram_id, "resumen_pepe", resumen_acumulado)

        rubro = data.get("rubro_detectado")
        if rubro: db.actualizar_adn(telegram_id, "rubro", rubro)
        
        dolor = data.get("dolor_detectado")
        if dolor: db.actualizar_adn(telegram_id, "dolor_principal", dolor)
        
        # Guardar en memoria general el estado de la checklist
        checklist_completo = data.get("checklist_completo", False)
        
        nuevo_estado = data.get("intentar_cambiar_estado", "PEPE_ACTIVO")
        if nuevo_estado != "PEPE_ACTIVO":
            db.actualizar_campo_usuario(telegram_id, "estado_onboarding", nuevo_estado)

        if checklist_completo and nuevo_estado == "PEPE_ACTIVO":
            teclado = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Faltan detalles", callback_data="pepe_mas_contexto")],
                [InlineKeyboardButton("🚀 Todo claro, avanzar con María", callback_data="pepe_avanzar_maria")]
            ])
            await target.reply_text(f"<b>Pepe:</b> {mensaje}\n\n<i>(Sistema: Pepe ha completado el perfil base)</i>", reply_markup=teclado, parse_mode="HTML")
        else:
            await target.reply_text(f"<b>Pepe:</b> {mensaje}", parse_mode="HTML")
            
    except Exception as e:
        log.error(f"Falla procesamiento Pepe: {e}")
        await target.reply_text("Pepe: ⚠️ Necesito un segundo para revisar mis notas (Error de parseo).")
        return False

    return True
