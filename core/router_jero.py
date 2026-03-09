from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from core import db
from core.logger_omnisciente import obtener_chismografo
from core.gemini_multimodal import describir_contenido_multimodal, procesar_texto_puro
from agentes.fase1_onboarding.sofy.sofy_router import manejar_onboarding
from agentes.fase1_onboarding.pepe.flow import manejar_pepe
from agentes.fase1_onboarding.maria.flow import manejar_maria
from agentes.fase1_onboarding.josefina.flow import manejar_josefina
from agentes.fase4_bunker.andrea.flow import manejar_andrea
from telegram.constants import ChatAction

log = obtener_chismografo("ROUTER_JERO_GRAPH")

class AgentState(TypedDict):
    update: object
    context: object
    telegram_id: int
    estado_actual: str
    contenido: str
    file_path: Optional[str]
    tools: Optional[list]
    proximo_paso: Optional[str]

async def call_sofy(state: AgentState):
    await manejar_onboarding(state["update"], state["context"], state["telegram_id"], state["estado_actual"], state["contenido"], tools=state.get("tools"))
    return state

async def intervention_jero(state: AgentState, agente_nombre: str):
    """Intervención de Jero cuando un agente falla (Error 429, 400, etc)"""
    target = state["update"].message if state["update"].message else state["update"].callback_query.message
    msg_error = f"💼 <b>Jero (CEO):</b> Hola, aquí Jero. He notado una pequeña inestabilidad en la conexión de {agente_nombre}. \n\nNo te preocupes, mis ingenieros ya están revisando el sistema. ¿Te parece si intentamos retomar esto en un minuto? O si prefieres, cuéntame algo más y veré cómo puedo ayudarte yo directamente."
    await target.reply_text(msg_error, parse_mode="HTML")
    return state

async def call_pepe(state: AgentState):
    success = await manejar_pepe(state["update"], state["context"], state["telegram_id"], state["contenido"], state["file_path"], tools=state.get("tools"))
    if not success:
        return await intervention_jero(state, "Pepe")
    return state

async def call_maria(state: AgentState):
    success = await manejar_maria(state["update"], state["context"], state["telegram_id"], state["contenido"], state["file_path"], tools=state.get("tools"))
    if not success:
        return await intervention_jero(state, "María")
    return state

async def call_josefina(state: AgentState):
    success = await manejar_josefina(state["update"], state["context"], state["telegram_id"], state["contenido"], state["file_path"], tools=state.get("tools"))
    if not success:
        return await intervention_jero(state, "Josefina")
    return state

async def call_bruno(state: AgentState):
    # Bruno flow placeholder - later we can implement it
    from core.gemini_multimodal import procesar_texto_puro
    from agentes.fase1_onboarding.bruno.rutinas import obtener_prompt
    
    prompt = obtener_prompt() + "\n\n" + "El usuario está en fase BRUNO completando el WBS."
    res = await procesar_texto_puro(prompt, state["contenido"], telegram_id=state["telegram_id"])
    db.guardar_memoria_hilo(state["telegram_id"], "SOCIO", state["contenido"])
    db.guardar_memoria_hilo(state["telegram_id"], "BRUNO", res)
    
    target = state["update"].message if state["update"].message else state["update"].callback_query.message
    
    # If Bruno finishes, he transitions the state to OPERACION_CONTINUA
    # Mock transition logic:
    if "WBS_CERRADO" in res:
         db.actualizar_campo_usuario(state["telegram_id"], "estado_onboarding", "OPERACION_CONTINUA")
         res = res.replace("WBS_CERRADO", "")
         
    await target.reply_text(f"📋 <b>Bruno:</b> {res}", parse_mode="HTML")
    return state

async def call_andrea(state: AgentState):
    success = await manejar_andrea(state["update"], state["context"], state["telegram_id"], state["contenido"])
    if not success:
        return await intervention_jero(state, "Dra. Andrea")
    return state
from google.genai import types as genai_types

# Esquema para el Ruteo Estructurado (Arquitectura 2026)
RoutingDecision = {
    "type": "OBJECT",
    "properties": {
        "siguiente_agente": {
            "type": "STRING",
            "enum": ["sofy", "pepe", "maria", "josefina", "bruno", "andrea", "fallback"],
            "description": "El nombre del agente que debe atender la petición."
        },
        "razonamiento": {
            "type": "STRING",
            "description": "Breve explicación de por qué se eligió este agente."
        }
    },
    "required": ["siguiente_agente", "razonamiento"]
}

async def call_supervisor_jero(state: AgentState):
    telegram_id = state["telegram_id"]
    
    # Cargamos el SOUL de Jero
    try:
        with open("agentes/jero/SOUL.md", "r", encoding="utf-8") as f:
            soul_jero = f.read()
    except:
        soul_jero = "Eres Jero, el CEO orquestador."

    # Jero analiza y decide el ruteo
    prompt_jero = f"""{soul_jero}\n\nESTADO ACTUAL: {state['estado_actual']}\nLISTA DE AGENTES: sofy, pepe, maria, josefina, bruno, andrea.\n\nRegla: Si hay duda o error, elige 'fallback'."""
    
    import json
    res_json = await procesar_texto_puro(
        prompt_jero, 
        state["contenido"], 
        telegram_id=telegram_id, 
        response_schema=RoutingDecision
    )
    
    try:
        decision = json.loads(res_json)
        state["proximo_paso"] = decision["siguiente_agente"]
        log.info(f"🎯 [DEERFLOW] Jero decidió: {state['proximo_paso']} (Razón: {decision['razonamiento']})")
    except Exception as e:
        log.error(f"❌ Error decodificando ruteo de Jero: {e}")
        state["proximo_paso"] = "fallback"

    return state

async def call_fallback(state: AgentState):
    target = state["update"].message if hasattr(state["update"], "message") and state["update"].message else state["update"].callback_query.message
    await target.reply_text("💼 <b>Jero (CEO):</b> He tenido una pequeña interferencia en la Mesa Directiva. No te preocupes, mis ingenieros ya están revisando el sistema. ¿Podrías repetirme lo último o intentar en un minuto?", parse_mode="HTML")
    return state

def routed_by_jero(state: AgentState):
    return state.get("proximo_paso", "sofy")

# Build LangGraph (Architecture 2026)
workflow = StateGraph(AgentState)
workflow.add_node("supervisor", call_supervisor_jero)
workflow.add_node("sofy", call_sofy)
workflow.add_node("pepe", call_pepe)
workflow.add_node("maria", call_maria)
workflow.add_node("josefina", call_josefina)
workflow.add_node("bruno", call_bruno)
workflow.add_node("andrea", call_andrea)
workflow.add_node("fallback", call_fallback)

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    routed_by_jero,
    {
        "sofy": "sofy",
        "pepe": "pepe",
        "maria": "maria",
        "josefina": "josefina",
        "bruno": "bruno",
        "andrea": "andrea",
        "fallback": "fallback"
    }
)

for node in ["sofy", "pepe", "maria", "josefina", "bruno", "andrea", "fallback"]: # Updated nodes to go to END
    workflow.add_edge(node, END)

app_graph = workflow.compile()

async def orquestar_mensaje(update, context, telegram_id, estado_actual, contenido, file_path=None):
    log.info(f"=== JERO (LANGGRAPH) EVALUANDO RUTA ===")
    
    texto_a_procesar = contenido
    msg_espera = None
    target = update.message if update.message else update.callback_query.message
    
    if file_path:
        log.info("Archivo/Audio detectado. Mandando feedback visual al usuario...")
        msg_espera = await target.reply_text("🎙️ <i>Sofy: Recibido. Estoy procesando tu audio/archivo, dame unos segundos...</i>", parse_mode="HTML")
        await context.bot.send_chat_action(chat_id=telegram_id, action=ChatAction.TYPING)
        
        transcripcion = await describir_contenido_multimodal(file_path)
        log.info(f"Transcripción exitosa.")
        texto_a_procesar = f"[Archivo Adjunto: {transcripcion}]\n\n" + (contenido if contenido else "")
        
        if msg_espera:
            await msg_espera.delete()
            
    log.info(f"Input Final a procesar: {texto_a_procesar[:100]}...")
    await context.bot.send_chat_action(chat_id=telegram_id, action=ChatAction.TYPING)
    
    # Invocamos el Grafo con el contenido puro
    # El agente decidirá mediante Function Calling si necesita leer la bóveda o el historial
    from core.tools_ms247 import global_tools
    
    initial_state = {
        "update": update,
        "context": context,
        "telegram_id": telegram_id,
        "estado_actual": estado_actual,
        "contenido": texto_a_procesar,
        "file_path": None,
        "tools": global_tools,
        "proximo_paso": None
    }
    
    # Invoke LangGraph
    await app_graph.ainvoke(initial_state)
    log.info(f"=== EJECUCIÓN GRÁFICA COMPLETADA ===")
