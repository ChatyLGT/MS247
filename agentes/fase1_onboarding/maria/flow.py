import re
import json
from core import db
import asyncio
from core import auditor
from core.gemini_multimodal import procesar_texto_puro
from core.grabadora import log_bot_response, log_forense, log_terminal
from core.logger_omnisciente import obtener_chismografo
from agentes.fase1_onboarding.maria import maria # Import corregido

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = obtener_chismografo("MARIA_FLOW")

async def manejar_maria(update, context, telegram_id, texto, file_path=None, tools=None):
    target = update.message if update.message else update.callback_query.message
    
    try:
        with open("agentes/fase1_onboarding/maria/SOUL.md", "r", encoding="utf-8") as f:
            soul = f.read()
    except Exception as e:
        soul = "Eres María, la arquitecta de la mesa directiva."

    # ADN Dinámico para María
    adn = db.obtener_adn_completo(telegram_id)
    rubro = adn.get("rubro", "tu negocio")
    dolor = adn.get("dolor_principal", "tus procesos")
    precio_previo = adn.get("precio_cotizado", 0)
    agentes_previos = adn.get("agentes_seleccionados", [])
    nivel_previo = adn.get("nivel_seleccionado", "")

    # Doctrina 2026: Prompt con inyección de ADN y Precios
    prompt = f"{soul}\n\nCONTEXTO DEL SOCIO:\nRubro: {rubro}\nDolor: {dolor}\n"
    if precio_previo > 0:
        prompt += f"\n💰 NOTA DE BACKEND: El sistema ha calculado un presupuesto de ${precio_previo} para los agentes {agentes_previos} en nivel {nivel_previo}. Comunícalo al usuario y busca el cierre para pasar a JOSEFINA_ACTIVA."
    
    prompt += "\n\nREGLAS 2026:\n1. Usa 'obtener_historial' para contexto.\n2. Usa 'leer_boveda' para el diagnóstico de Pepe."
    
    res_ia = await procesar_texto_puro(prompt, texto, modo_json=True, telegram_id=telegram_id, tools=tools)
    
    if res_ia.startswith("⚠️ [SISTEMA]"):
        log_forense("MARIA_ERROR", res_ia, telegram_id)
        return False

    log_forense("MARIA", res_ia, telegram_id)
    print(f"\n--- 🕵️ FORENSE MARIA RAW ---\n{res_ia}\n-----------------------------\n")

    try:
        # Limpieza de markdown si existe
        clean_res = res_ia.strip()
        if clean_res.startswith("```json"):
            clean_res = clean_res.replace("```json", "").replace("```", "").strip()
        elif clean_res.startswith("```"):
            clean_res = clean_res.replace("```", "").strip()
            
        data = json.loads(clean_res)
        mensaje = data.get("mensaje", "Interesante, cuéntame más.")
        fase = data.get("fase_venta", "EDUCANDO")
        datos = data.get("datos_cotizacion", {})
        nuevo_estado = data.get("intentar_cambiar_estado", "MARIA_ACTIVA")
        
        db.guardar_memoria_hilo(telegram_id, "SOCIO", texto)
        db.guardar_memoria_hilo(telegram_id, "MARIA", mensaje)
        
        # Interceptor de Cotización
        if fase == "COTIZANDO" and datos:
            agentes = datos.get("agentes", [])
            nivel = datos.get("nivel_intervencion", "Maker")
            # Cálculo Vera-020: $15 Base + $10 por cada agente
            precio = 15 + (len(agentes) * 10)
            
            db.actualizar_adn(telegram_id, "precio_cotizado", precio)
            db.actualizar_adn(telegram_id, "agentes_seleccionados", agentes)
            db.actualizar_adn(telegram_id, "nivel_seleccionado", nivel)
            log_terminal("COTIZACION", telegram_id, f"Precio: ${precio} para {agentes}")

        if nuevo_estado and nuevo_estado != "MARIA_ACTIVA":
            db.actualizar_campo_usuario(telegram_id, "estado_onboarding", nuevo_estado)

        await target.reply_text(f"<b>María:</b> {mensaje}", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error parseando JSON de Maria: {e}")
        db.guardar_memoria_hilo(telegram_id, "SOCIO", texto)
        db.guardar_memoria_hilo(telegram_id, "MARIA", res_ia)
        # Intento de extraer mensaje vía regex como último recurso
        match = re.search(r'"mensaje":\s*"([^"]+)"', res_ia)
        msg_final = match.group(1) if match else res_ia
        await target.reply_text(f"<b>María:</b> {msg_final}", parse_mode="HTML")

    return True
