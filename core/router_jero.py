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

async def call_sofy(state: AgentState):
    await manejar_onboarding(state["update"], state["context"], state["telegram_id"], state["estado_actual"], state["contenido"])
    return state

async def call_pepe(state: AgentState):
    await manejar_pepe(state["update"], state["context"], state["telegram_id"], state["contenido"], state["file_path"])
    return state

async def call_maria(state: AgentState):
    await manejar_maria(state["update"], state["context"], state["telegram_id"], state["contenido"], state["file_path"])
    return state

async def call_josefina(state: AgentState):
    await manejar_josefina(state["update"], state["context"], state["telegram_id"], state["contenido"], state["file_path"])
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
    await manejar_andrea(state["update"], state["context"], state["telegram_id"], state["contenido"])
    return state

async def call_supervisor_jero(state: AgentState):
    telegram_id = state["telegram_id"]
    adn = db.obtener_adn_completo(telegram_id) or {}
    
    # JERO: Dynamic Instantiation based on adn_negocios
    # We assemble the prompt dynamically reading the db instead of static files like ana.py.
    personalidad = adn.get('personalidad_agentes', 'Equipo profesional 24/7.')
    estructura = adn.get('estructura_equipo', 'Sockets Genéricos Activos')
    
    system_prompt = f"""Eres JERO, el CEO y Orquestador de la Mesa Directiva de MisSocios24/7.
ADN de la Empresa: {adn.get('nombre_empresa')} | Rubro: {adn.get('rubro')}
Dolor Principal: {adn.get('dolor_principal')}

Sockets Habilitados por María: {estructura}
Personalidad Inyectada por Josefina: {personalidad}

Tu misión es resolver la petición del usuario '{state['contenido']}'. 
1. Evalúa qué socket (especialista) necesita responder (Ej: CFO, Legal, Operaciones).
2. Asume ese rol ORQUESTADO o solicita la data al especialista ficticiamente y devuélvela al usuario en un solo mensaje colegiado.
"""
    from core.sandbox import ejecutar_agente_sandbox
    res = await ejecutar_agente_sandbox(system_prompt, state["contenido"], telegram_id=telegram_id)
    
    db.guardar_memoria_hilo(telegram_id, "SOCIO", state["contenido"])
    db.guardar_memoria_hilo(telegram_id, "JERO_MESA_DIRECTIVA", res)

    target = state["update"].message if hasattr(state["update"], "message") and state["update"].message else state["update"].callback_query.message
    await target.reply_text(f"💼 <b>Jero (CEO):</b> {res}", parse_mode="HTML")
    return state

def router_logic(state: AgentState):
    estado = state["estado_actual"]
    
    # Enforcing strict state machine. Blocking Jero.
    if estado in ["NUEVO", "WHATSAPP", "TYC", "DATOS"]: return "sofy"
    if estado == "PEPE_ACTIVO": return "pepe"
    if estado == "MARIA_ACTIVO": return "maria"
    if estado == "JOSEFINA_ACTIVO": return "josefina"
    if estado == "BRUNO_ACTIVO": return "bruno"
    if estado == "ANDREA_ACTIVO" or estado == "EMERGENCY_COACHING": return "andrea"
    
    # If state is OPERACION_CONTINUA but ADN is incomplete (e.g. no WBS or missing structure)
    telegram_id = state["telegram_id"]
    adn = db.obtener_adn_completo(telegram_id) or {}
    # Validation logic: if no structure, block. (Assume missing structure means incomplete)
    if estado == "OPERACION_CONTINUA" and not adn.get('estructura_equipo'):
        # Force fallback to Maria
        db.actualizar_campo_usuario(telegram_id, "estado_onboarding", "MARIA_ACTIVO")
        return "maria"
        
    if estado == "OPERACION_CONTINUA": return "supervisor"
    
    return "sofy"

# Build LangGraph
workflow = StateGraph(AgentState)
workflow.add_node("sofy", call_sofy)
workflow.add_node("pepe", call_pepe)
workflow.add_node("maria", call_maria)
workflow.add_node("josefina", call_josefina)
workflow.add_node("bruno", call_bruno)
workflow.add_node("andrea", call_andrea)
workflow.add_node("supervisor", call_supervisor_jero)

workflow.set_conditional_entry_point(
    router_logic,
    {
        "sofy": "sofy",
        "pepe": "pepe",
        "maria": "maria",
        "josefina": "josefina",
        "bruno": "bruno",
        "andrea": "andrea",
        "supervisor": "supervisor"
    }
)

for node in ["sofy", "pepe", "maria", "josefina", "bruno", "andrea", "supervisor"]:
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
    
    initial_state = {
        "update": update,
        "context": context,
        "telegram_id": telegram_id,
        "estado_actual": estado_actual,
        "contenido": texto_a_procesar,
        "file_path": None # Already processed
    }
    
    # Invoke LangGraph
    await app_graph.ainvoke(initial_state)
    log.info(f"=== EJECUCIÓN GRÁFICA COMPLETADA ===")
