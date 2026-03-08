from core import db
from core.gemini_multimodal import procesar_texto_puro
from agentes.fase1_onboarding.sofy import sofy.sofy_router import manejar_onboarding

async def verificar_intervencion_sofy(update, context, telegram_id, estado, contenido):
    # Solo monitoreamos si NO estás ya con Andrea
    if estado == "ANDREA_ACTIVO":
        return False

    # Prompt ultra-rápido para que Sofy actúe como sensor
    prompt_sensor = f"""
    Eres SOFÍA, la Hostess. Tu función es vigilar la integridad del socio.
    Analiza si el siguiente mensaje muestra vulnerabilidad emocional, crisis o pedido de ayuda personal.
    Si es así, responde ÚNICAMENTE con la palabra: INTERVENIR.
    Si el mensaje es puramente de negocios o casual, responde: PASAR.
    
    MENSAJE: {contenido}
    """
    
    
    decision = await procesar_texto_puro(prompt_sensor, contenido)
    print(f"   🎭 SOFY MONITOR: Analizando mensaje... ¿Intervención? -> {decision.strip()}")

    
    if "INTERVENIR" in decision.upper():
        print(f"🚨 LOG: Sofy detecta crisis en estado {estado}. Interviniendo...")
        # Forzamos a que Sofy tome el control para hacer el pase a Andrea
        # Le mandamos un texto que gatille su regla de [ANDREA]
        await manejar_onboarding(update, context, telegram_id, estado, f"{contenido} [Sofy, necesito a la doctora]")
        return True
    
    return False
