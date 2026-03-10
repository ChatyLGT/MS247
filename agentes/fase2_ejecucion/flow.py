from core import db
from core.gemini_multimodal import procesar_texto_puro
from core.grabadora import log_terminal, log_bot_response

async def manejar_operativo(update, context, telegram_id, contenido):
    # PILAR 1: Recuperar el equipo
    adn = db.obtener_adn_completo(telegram_id)
    equipo = adn.get("equipo", [])
    
    if not equipo:
        return False

    # PILAR 2: Construir el prompt de la Sala de Juntas Operativa
    equipo_str = "\n".join([
        f"- {a['nombre_agente']} ({a['rol_socket']}): {a['personalidad']}. Estilo: {a.get('estilo_narrativo', 'Corporativo')}" 
        for a in equipo
    ])

    prompt_operativo = f"""Eres la MESA DIRECTIVA del usuario. Actuas como los agentes contratados.
EQUIPO DISPONIBLE:
{equipo_str}

TAREA: Responde a la peticion del usuario: "{contenido}"
REGLAS:
1. Si el usuario se dirige a uno o varios agentes especificos, responde COMO ELLOS.
2. Si el usuario pide una tarea administrativa/financiera, los agentes deben colaborar.
3. ESTILO: Respeta estrictamente la personalidad. Si un agente es Dr. House, es cinico y rudo. Si es Tarantino, es epico.
4. PROHIBICION TOTAL: CERO EMOJIS en las respuestas de los agentes.
5. FORMATO: Devuelve un JSON con un array de dialogos:
[
  {{"agente": "Nombre del Agente", "texto": "..."}},
  ...
]
Responde SOLO con el JSON."""

    res_ia = await procesar_texto_puro(prompt_operativo, contenido, telegram_id=telegram_id)
    
    try:
        import json
        res_ia = res_ia.strip()
        if "```json" in res_ia: res_ia = res_ia.split("```json")[1].split("```")[0].strip()
        elif "```" in res_ia: res_ia = res_ia.split("```")[1].split("```")[0].strip()
        
        guion = json.loads(res_ia)
        # Solo logueamos en el chismografo, pero NO enviamos a Telegram. Jero auditara primero.
        for linea in guion:
            log_bot_response(linea.get("agente", "Especialista"), linea.get("texto", "..."), telegram_id=telegram_id)
            
        return guion # Retornamos la lista de dicts
    except Exception as e:
        print(f"Error en flow operativo: {e}")
        return None
