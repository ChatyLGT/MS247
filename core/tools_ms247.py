from google.genai import types
from core import db, obsidian, rag_service

# --- DECLARACIONES DE HERRAMIENTAS (Function Declarations) ---

tool_leer_boveda = types.FunctionDeclaration(
    name="leer_boveda",
    description="Consulta documentos específicos en la bóveda de Obsidian del usuario (ej: '02_diagnostico_pepe.md').",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "documento": types.Schema(type=types.Type.STRING, description="El nombre del archivo .md a consultar."),
        },
        required=["documento"],
    ),
)

tool_consultar_rag = types.FunctionDeclaration(
    name="consultar_rag",
    description="Busca información en el manual maestro o en la memoria de largo plazo del sistema mediante RAG.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "query": types.Schema(type=types.Type.STRING, description="La pregunta o concepto a buscar en la base de conocimientos."),
        },
        required=["query"],
    ),
)

tool_obtener_historial = types.FunctionDeclaration(
    name="obtener_historial",
    description="Recupera los últimos mensajes de la conversación actual para tener contexto del flujo.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "limite": types.Schema(type=types.Type.INTEGER, description="Cantidad de mensajes a recuperar (default 5)."),
        },
    ),
)

tool_leer_cuestionario = types.FunctionDeclaration(
    name="leer_cuestionario",
    description="Lee las preguntas del cuestionario de diagnóstico por niveles (ej: 'Nivel 1A', 'Nivel 2B').",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "nivel": types.Schema(type=types.Type.STRING, description="El nivel o sección específica a leer."),
        },
        required=["nivel"],
    ),
)

# Empaquetamos en un objeto Tool
global_tools = [
    types.Tool(function_declarations=[
        tool_leer_boveda, 
        tool_consultar_rag, 
        tool_obtener_historial, 
        tool_leer_cuestionario
    ])
]

# --- IMPLEMENTACIONES DE LOS PUENTES (Executors) ---

def ejecutar_tool_leer_boveda(telegram_id: int, documento: str) -> str:
    print(f"🛠️ [TOOLS] Leyendo bóveda: {documento}")
    return obsidian.leer_documento(telegram_id, documento)

def ejecutar_tool_consultar_rag(query: str) -> str:
    print(f"🛠️ [TOOLS] Consultando RAG: {query}")
    return rag_service.consultar_rag(query)

def ejecutar_tool_obtener_historial(telegram_id: int, limite: int = 5) -> str:
    print(f"🛠️ [TOOLS] Recuperando historial (limite={limite})")
    adn = db.obtener_adn_completo(telegram_id)
    historial = adn.get("historial_reciente") or []
    reciente = historial[-limite:] if isinstance(historial, list) else []
    return "\n".join([f"{m['rol']}: {m['txt']}" for m in reciente])

def ejecutar_tool_leer_cuestionario(nivel: str) -> str:
    import os
    print(f"🛠️ [TOOLS] Leyendo cuestionario Nivel: {nivel}")
    path = "knowledge_base/cuestionario_pepe_150.md"
    if not os.path.exists(path): return "Cuestionario no encontrado."
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        import re
        # Búsqueda por header ## Nivel
        match = re.search(f"(## {nivel}.*?)(?=##|$)", content, re.DOTALL | re.IGNORECASE)
        if match:
             return match.group(1).strip()
        return "Nivel no encontrado. Prueba con 'Nivel 1A', 'Nivel 1B', etc. o 'INTRODUCCION'"

# Mapeo de nombres a funciones ejecutoras
handlers = {
    "leer_boveda": ejecutar_tool_leer_boveda,
    "consultar_rag": ejecutar_tool_consultar_rag,
    "obtener_historial": ejecutar_tool_obtener_historial,
    "leer_cuestionario": ejecutar_tool_leer_cuestionario
}
