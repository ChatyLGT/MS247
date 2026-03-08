from google.genai import types

from core.sandbox import (
    tool_leer_wbs,
    tool_actualizar_wbs,
    sandbox_tools
)

def test_leer_wbs_declaration():
    """Valida la estructura de la herramienta leer_wbs."""
    assert tool_leer_wbs.name == "leer_wbs"
    assert "proyecto_id" in tool_leer_wbs.parameters.properties

def test_actualizar_wbs_declaration():
    """Valida la estructura de la herramienta actualizar_wbs."""
    assert tool_actualizar_wbs.name == "actualizar_wbs"
    assert "tarea_id" in tool_actualizar_wbs.parameters.properties
    assert "nuevo_estado" in tool_actualizar_wbs.parameters.properties

def test_sandbox_tools_contains_tools():
    """Valida que las herramientas se han exportado correctamente."""
    # sandbox_tools[0] = code_execution
    # sandbox_tools[1] = object with function declarations
    tools_list = sandbox_tools[1].function_declarations
    tool_names = [tool.name for tool in tools_list]
    assert "leer_wbs" in tool_names
    assert "actualizar_wbs" in tool_names
