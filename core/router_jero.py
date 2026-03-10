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
from agentes.fase2_ejecucion.flow import manejar_operativo
from core.stripe_pagos import ejecutar_cobro_upgrade, StripeDeclinedError
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
    response_content: Optional[list]
    qa_pass: Optional[bool]
    retry_count: int
    audit_pass: Optional[bool]
    audit_feedback: Optional[str]
    proposal_context: Optional[str]
    pending_approval: Optional[bool]

async def call_sofy(state: AgentState):
    await manejar_onboarding(state["update"], state["context"], state["telegram_id"], state["estado_actual"], state["contenido"], tools=state.get("tools"))
    return state

async def intervention_jero(state: AgentState, agente_nombre: str):
    target = state["update"].message if state["update"].message else state["update"].callback_query.message
    msg_error = f"💼 <b>Jero (CEO):</b> Hola, aquí Jero. He notado una pequeña inestabilidad en la conexión de {agente_nombre}. \n\nNo te preocupes, mis ingenieros ya están revisando el sistema."
    await target.reply_text(msg_error, parse_mode="HTML")
    return state

async def call_pepe(state: AgentState):
    success = await manejar_pepe(state["update"], state["context"], state["telegram_id"], state["contenido"], state["file_path"], tools=state.get("tools"))
    if not success: return await intervention_jero(state, "Pepe")
    return state

async def call_maria(state: AgentState):
    success = await manejar_maria(state["update"], state["context"], state["telegram_id"], state["contenido"], state["file_path"], tools=state.get("tools"))
    if not success: return await intervention_jero(state, "María")
    return state

async def call_josefina(state: AgentState):
    success = await manejar_josefina(state["update"], state["context"], state["telegram_id"], state["contenido"], state["file_path"], tools=state.get("tools"))
    if not success: return await intervention_jero(state, "Josefina")
    return state

async def call_bruno(state: AgentState):
    from agentes.fase1_onboarding.bruno.flow import manejar_bruno
    success = await manejar_bruno(state["update"], state["context"], state["telegram_id"], state["contenido"], tools=state.get("tools"))
    if not success: return await intervention_jero(state, "Bruno")
    return state

async def call_andrea(state: AgentState):
    success = await manejar_andrea(state["update"], state["context"], state["telegram_id"], state["contenido"])
    if not success: return await intervention_jero(state, "Dra. Andrea")
    return state

async def call_operativo(state: AgentState):
    # ETAPA 3: Mediacion de Conflictos.
    # Si el mensaje incluye "bajar precios", Jero inyecta una nota de aviso a los agentes.
    contexto_jero = ""
    if "baja los precios" in state["contenido"].lower() or "bajar precios" in state["contenido"].lower():
        contexto_jero = "\n[NOTA DE JERO (CEO): Especialistas, cuidado con el margen de rentabilidad y los contratos legales vigentes. Javier y Ana deben dar su opinion antes de decidir.]"
    
    dialogos = await manejar_operativo(state["update"], state["context"], state["telegram_id"], state["contenido"] + contexto_jero)
    if not dialogos: return await intervention_jero(state, "Equipo Operativo")
    
    state["response_content"] = dialogos
    return state

async def call_qa_jero(state: AgentState):
    """ETAPA 1: Filtro Anti-Generico de Jero"""
    if "response_content" not in state or not state["response_content"]:
        state["qa_pass"] = True
        return state
    
    lista_negra = ["innovador", "descubre", "sumergete", "en el vasto mundo", "potencializa", "una amplia gama", "esta aqui para ayudarte"]
    
    full_text = " ".join([d.get("texto", "").lower() for d in state["response_content"]])
    found = [word for word in lista_negra if word in full_text]
    
    if found:
        log.warning(f"[QA_JERO] Basura IA detectada: {found}")
        state["qa_pass"] = False
        state["retry_count"] += 1
        # Feedback rudo de Jero
        state["contenido"] += f"\n[FEEDBACK DE JERO: Este borradores es BASURA GENERICA. Quitame las palabras IA como {found}. Se directo, rudo y profesional. Reescribe ahora (Intento {state['retry_count']}).]"
    else:
        state["qa_pass"] = True
        
    return state

async def call_delivery(state: AgentState):
    """Nodo final de entrega a Telegram"""
    telegram_id = state["telegram_id"]
    context = state["context"]

    # Si hay feedback de auditoria pendiente (HITL)
    if state.get("audit_pass") is False and state.get("audit_feedback"):
        await context.bot.send_message(chat_id=telegram_id, text=f"⚠️ <b>Audit Guardians:</b>\n{state['audit_feedback']}", parse_mode="HTML")
        db.actualizar_campo_usuario(telegram_id, "estado_onboarding", "WAITING_USER_APPROVAL")
        return state

    if not state.get("response_content"): return state
    
    for linea in state["response_content"]:
        nombre = linea.get("agente", "Especialista")
        texto = linea.get("texto", "...")
        await context.bot.send_message(chat_id=telegram_id, text=f"🤖 <b>{nombre}:</b> {texto}", parse_mode="HTML")
    return state

async def call_audit_guardians(state: AgentState):
    """PILAR 1: Maria y Pepe auditan la propuesta antes de ejecutar."""
    telegram_id = state["telegram_id"]
    adn = db.obtener_adn_completo(telegram_id)
    equipo = adn.get("equipo", [])
    rubro = adn.get("rubro", "Niche Genérico")
    
    prompt_audit = f"""Eres un SISTEMA DE AUDITORÍA (María de Finanzas y Pepe de ADN).
Analiza el pedido del usuario: "{state['contenido']}"
Rubro actual: {rubro}
Equipo actual (Sockets): {[a['rol_socket'] for a in equipo]}

REGLAS:
1. Si el pedido implica un producto/servicio ajeno al rubro, Pepe debe marcar INCOHERENCIA.
2. Si el pedido requiere un especialista NO contratado (ej. pide Marketing y no hay CMO), María debe detectar el desvío.
3. El costo de un nuevo socket es $10 extra sobre la base.

FORMATO JSON:
{{
  "audit_pass": bool,
  "msg_hitl": "Mensaje rudo para el usuario si falla",
  "razon": "string",
  "upselling_cost": int,
  "nuevo_especialista": "string or null",
  "nueva_filosofia": "string or null"
}}
"""
    try:
        res_json = await procesar_texto_puro(prompt_audit, "Auditoría de Guardians", telegram_id=telegram_id)
        import json
        audit = json.loads(res_json.strip('```json').strip())
        state["audit_pass"] = audit["audit_pass"]
        state["audit_feedback"] = audit["msg_hitl"]
        if not state["audit_pass"]:
            state["pending_approval"] = True
            # PERSISTENCIA: Guardar para HITL
            propuesta = {
                "contenido_original": state["contenido"],
                "nuevo_especialista": audit.get("nuevo_especialista"),
                "nueva_filosofia": audit.get("nueva_filosofia"),
                "costo": audit.get("upselling_cost")
            }
            db.actualizar_adn(telegram_id, "propuesta_pendiente", json.dumps(propuesta))
    except Exception as e:
        log.error(f"Error en Audit Guardians: {e}")
        state["audit_pass"] = True # Por seguridad si falla la IA
    return state

def jero_audit_condition(state: AgentState):
    if state.get("qa_pass") is False and state.get("retry_count", 0) < 2:
        return "operativo"
    return "delivery"

def guardians_choice(state: AgentState):
    if state.get("audit_pass") is False:
        return "delivery" # Para mostrar el aviso de HITL
    return "operativo"

async def call_kickoff(state: AgentState):
    import asyncio
    telegram_id = state["telegram_id"]
    context = state["context"]
    adn = db.obtener_adn_completo(telegram_id)
    equipo = adn.get("equipo", [])
    empresa = adn.get("nombre_empresa", "tu negocio")
    equipo_str = "\n".join([f"- {a['nombre_agente']} ({a['rol_socket']}): {a['personalidad']}" for a in equipo])
    
    prompt_kickoff = f"Eres Jero, CEO. Guion de Kickoff para '{empresa}'. Equipo:\n{equipo_str}\n\nFORMATO JSON: [{{'agente': '...', 'texto': '...'}}]"
    res_ia = await procesar_texto_puro(prompt_kickoff, "Kickoff", telegram_id=telegram_id)
    
    try:
        import json
        res_ia = res_ia.strip()
        if "```json" in res_ia: res_ia = res_ia.split("```json")[1].split("```")[0].strip()
        guion = json.loads(res_ia)
        for linea in guion:
            nombre = linea.get("agente", "Jero")
            texto = linea.get("texto", "...")
            await asyncio.sleep(1)
            await context.bot.send_message(chat_id=telegram_id, text=f"🤖 <b>{nombre}:</b> {texto}", parse_mode="HTML")
        db.actualizar_campo_usuario(telegram_id, "estado_onboarding", "OPERACION_CONTINUA")
    except:
        await context.bot.send_message(chat_id=telegram_id, text="💼 <b>Jero:</b> ¡Bienvenidos! Arrancamos.")
    return state

RoutingDecision = {
    "type": "OBJECT",
    "properties": {
        "siguiente_agente": {
            "type": "STRING",
            "enum": ["sofy", "pepe", "maria", "josefina", "bruno", "andrea", "kickoff", "operativo", "fallback"]
        },
        "razonamiento": {"type": "STRING"}
    },
    "required": ["siguiente_agente", "razonamiento"]
}

async def call_supervisor_jero(state: AgentState):
    telegram_id = state["telegram_id"]
    adn = db.obtener_adn_completo(telegram_id)
    equipo = adn.get("equipo", [])
    equipo_nombres = ", ".join([a["nombre_agente"] for a in equipo])

    prompt_jero = f"""Eres Jero, CEO.
ESTADO ACTUAL: {state['estado_actual']}
EQUIPO OPERATIVO: {equipo_nombres}

REGLAS DE RUTEO:
1. Si el usuario pide hablar con alguien de su EQUIPO o pide una tarea operativa (marketing, legal, finanzas, ventas, etc), rutea a 'operativo'.
2. Si el mensaje es una crisis ('no puedo mas'), rutea a 'andrea'.
3. Si el estado es KICKOFF, rutea a 'kickoff'.
4. Si es Onboarding inicial, rutea al agente correspondiente (sofy, pepe, maria, josefina, bruno)."""

    import json
    res_json = await procesar_texto_puro(prompt_jero, state["contenido"], telegram_id=telegram_id, response_schema=RoutingDecision)
    try:
        decision = json.loads(res_json)
        state["proximo_paso"] = decision["siguiente_agente"]
        log.info(f"[DEERFLOW] Jero decidio: {state['proximo_paso']}")
    except:
        state["proximo_paso"] = "fallback"
    return state

async def call_fallback(state: AgentState):
    target = state["update"].message if hasattr(state["update"], "message") else state["update"].callback_query.message
    await target.reply_text("💼 <b>Jero:</b> ¿Podrías repetirme eso?", parse_mode="HTML")
    return state

def routed_by_jero(state: AgentState): return state.get("proximo_paso", "sofy")

workflow = StateGraph(AgentState)
workflow.add_node("supervisor", call_supervisor_jero)
workflow.add_node("qa_jero", call_qa_jero)
workflow.add_node("delivery", call_delivery)
workflow.add_node("audit_guardians", call_audit_guardians)

for n in ["sofy", "pepe", "maria", "josefina", "bruno", "andrea", "kickoff", "operativo", "fallback"]:
    workflow.add_node(n, globals()[f"call_{n}"])

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges("supervisor", routed_by_jero, {
    "operativo": "audit_guardians", # Jero propone, Guardians auditan
    "sofy": "sofy", "pepe": "pepe", "maria": "maria", "josefina": "josefina", 
    "bruno": "bruno", "andrea": "andrea", "kickoff": "kickoff", "fallback": "fallback"
})

workflow.add_conditional_edges("audit_guardians", guardians_choice, {
    "operativo": "operativo",
    "delivery": "delivery" # Si falla, enviamos el mensaje de autorizacion
})

# Flujo post-operativo para Auditoria
workflow.add_edge("operativo", "qa_jero")
workflow.add_conditional_edges("qa_jero", jero_audit_condition, {"operativo": "operativo", "delivery": "delivery"})
workflow.add_edge("delivery", END)

# Los demas nodos van a END directo
for n in ["sofy", "pepe", "maria", "josefina", "bruno", "andrea", "kickoff", "fallback"]: workflow.add_edge(n, END)

app_graph = workflow.compile()

async def orquestar_mensaje(update, context, telegram_id, estado_actual, contenido, file_path=None):
    log.info("=== JERO ROUTER START ===")
    texto = contenido
    
    # PILAR 3: Resolucion Dinamica
    if estado_actual == "WAITING_USER_APPROVAL":
        adn = db.obtener_adn_completo(telegram_id)
        import json
        propuesta = adn.get("propuesta_pendiente")
        # Si es un string JSON, parsear
        if isinstance(propuesta, str): propuesta = json.loads(propuesta)
        
        if propuesta:
            if "si" in contenido.lower() or "acept" in contenido.lower() or "vale" in contenido.lower():
                # LUZ VERDE -> Intentar Cobro
                costo = propuesta.get("costo", 10)
                try:
                    pago = await ejecutar_cobro_upgrade(telegram_id, costo, f"Upgrade: {propuesta.get('nuevo_especialista', 'Servicio Extra')}")
                    
                    # Cobro Exitoso
                    msg_jero = f"[LUZ VERDE DEL SOCIO: Pago de ${costo} procesado. Ejecuta la propuesta original: {propuesta['contenido_original']}]"
                    
                    if propuesta.get("nuevo_especialista"):
                         db.agregar_agente_equipo(telegram_id, propuesta["nuevo_especialista"], "Maker", propuesta["nuevo_especialista"], "Eficiente")
                    
                    # Generamos el recibo de Sofy inmediatamente
                    recibo_sofy = f"💼 <b>Sofy (Account Manager):</b> ¡Pago procesado con éxito! He sumado a {propuesta.get('nuevo_especialista', 'tu nuevo agente')} a tu equipo y cargado ${costo} a tu tarjeta terminada en {pago['last4']}."
                    await context.bot.send_message(chat_id=telegram_id, text=recibo_sofy, parse_mode="HTML")
                    
                    texto = msg_jero
                    db.actualizar_campo_usuario(telegram_id, "estado_onboarding", "OPERACION_CONTINUA")
                    db.actualizar_adn(telegram_id, "propuesta_pendiente", None)
                    
                except StripeDeclinedError:
                    # Cobro Fallido -> Cero Costo Alternativa
                    msg_ia = f"[RECHAZO DE STRIPE: La tarjeta del cliente fue declinada. Propón una alternativa CERO COSTO obligatoria para la peticion inicial: {propuesta['contenido_original']}]"
                    texto = msg_ia
                    db.actualizar_campo_usuario(telegram_id, "estado_onboarding", "OPERACION_CONTINUA")
                    db.actualizar_adn(telegram_id, "propuesta_pendiente", None)
            else:
                # RECHAZO
                msg_ia = f"[RECHAZO DEL SOCIO: No se autoriza el cambio. Propón una alternativa que NO requiera inversión extra ni cambios filosóficos para: {propuesta['contenido_original']}]"
                texto = msg_ia
                db.actualizar_campo_usuario(telegram_id, "estado_onboarding", "OPERACION_CONTINUA")
                db.actualizar_adn(telegram_id, "propuesta_pendiente", None)

    if file_path:
        transcripcion = await describir_contenido_multimodal(file_path)
        texto = f"[Archivo: {transcripcion}]\n" + (texto or "")
    
    from core.tools_ms247 import global_tools
    initial_state = {
        "update": update, "context": context, "telegram_id": telegram_id,
        "estado_actual": estado_actual, "contenido": texto, "file_path": file_path,
        "tools": global_tools, "proximo_paso": None, "retry_count": 0,
        "response_content": None, "qa_pass": None,
        "audit_pass": None, "audit_feedback": None, "pending_approval": False
    }
    await app_graph.ainvoke(initial_state)
