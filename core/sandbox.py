from google.genai import types

# Declaraciones de herramientas para usar en `tools=` en la llamada a Gemini
# Declaramos Code Execution (Makers Sandbox aislado por Google) de manera nativa
tool_code_execution = {"code_execution": {}}

tool_leer_wbs = types.FunctionDeclaration(
    name="leer_wbs",
    description="Lee las tareas del Work Breakdown Structure (WBS) de un proyecto determinado en PostgreSQL.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "proyecto_id": types.Schema(type=types.Type.INTEGER, description="El ID numérico del proyecto asociado."),
        },
        required=["proyecto_id"],
    ),
)

tool_actualizar_wbs = types.FunctionDeclaration(
    name="actualizar_wbs",
    description="Actualiza el estado de una tarea específica en el WBS.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "tarea_id": types.Schema(type=types.Type.INTEGER, description="El ID de la tarea a modificar."),
            "nuevo_estado": types.Schema(type=types.Type.STRING, description="El nuevo estado, ej: 'COMPLETADO', 'EN_PROGRESO'."),
        },
        required=["tarea_id", "nuevo_estado"],
    ),
)

sandbox_tools = [
    tool_code_execution, 
    types.Tool(function_declarations=[tool_leer_wbs, tool_actualizar_wbs])
]

# Funciones puente para invocar la base de datos cuando Gemini devuelve Function Calls
def ejecutar_tool_leer_wbs(proyecto_id: int) -> str:
    from core.db import get_connection
    from psycopg2.extras import RealDictCursor
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM tareas_wbs WHERE proyecto_id = %s", (proyecto_id,))
        tareas = cur.fetchall()
        cur.close()
        conn.close()
        return str(tareas)
    except Exception as e:
        return f"Error leyendo WBS: {e}"

def ejecutar_tool_actualizar_wbs(tarea_id: int, nuevo_estado: str) -> str:
    from core.db import get_connection
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE tareas_wbs SET estado = %s WHERE id = %s", (nuevo_estado, tarea_id))
        conn.commit()
        cur.close()
        conn.close()
        return "Tarea actualizada exitosamente."
    except Exception as e:
        return f"Error actualizando Tarea WBS: {e}"

async def ejecutar_agente_sandbox(prompt_sistema: str, texto_usuario: str, telegram_id: int) -> str:
    from google import genai
    from google.genai import types
    from core.gemini_multimodal import client
    import asyncio
    from core import db
    
    config = types.GenerateContentConfig(
        tools=sandbox_tools,
        temperature=0.4
    )
    
    try:
        # Create a chat session to handle multi-turn function calling
        chat = client.aio.chats.create(model="gemini-2.0-flash", config=config)
        
        # We pass the system prompt as the first message or configure it in system_instruction (if using SDK correctly)
        # For simplicity, we inject it into the first user message:
        full_prompt = f"INSTINTO/SISTEMA:\n{prompt_sistema}\n\nUSUARIO:\n{texto_usuario}"
        
        response = await chat.send_message(full_prompt)
        
        # Telemetría de la primera llamada
        if response.usage_metadata:
            asyncio.create_task(asyncio.to_thread(db.restar_tokens_gasolina, telegram_id, response.usage_metadata.total_token_count))
            
        # Loop for handling custom function calls
        while response.function_calls:
            for function_call in response.function_calls:
                name = function_call.name
                args = function_call.args
                print(f"🛠️ [SANDBOX] Gemini solicita ejecutar: {name} con {args}")
                
                result_str = ""
                if name == "leer_wbs":
                    result_str = ejecutar_tool_leer_wbs(int(args.get("proyecto_id", 0)))
                elif name == "actualizar_wbs":
                    result_str = ejecutar_tool_actualizar_wbs(int(args.get("tarea_id", 0)), args.get("nuevo_estado", ""))
                else:
                    result_str = f"Error: Tool {name} no implementada."
                    
                # Devolver el resultado de la función al chat
                function_response = types.Part.from_function_response(
                    name=name,
                    response={"result": result_str}
                )
                
                response = await chat.send_message(function_response)
                
                if response.usage_metadata:
                    asyncio.create_task(asyncio.to_thread(db.restar_tokens_gasolina, telegram_id, response.usage_metadata.total_token_count))
                    
        # When loop is done or if it was just text / code_execution:
        return response.text
    except Exception as e:
        print(f"🔥 ERROR SANDBOX: {e}")
        return "Error en el Sandbox de Ejecución."
