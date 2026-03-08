import os
from core import matriz_agentes

def obtener_prompt(telegram_id):
    perfil = matriz_agentes.obtener_personalidad('JOSEFINA')
    if not perfil:
        return "Eres Josefina, pero hubo un error cargando tu matriz."
    
    formulario = ""
    if os.path.exists("knowledge_base/bi_josefina.txt"):
        with open("knowledge_base/bi_josefina.txt", "r", encoding="utf-8") as f:
            formulario = f.read()
    
    prompt = f"""
    SOUL_BACKSTORY: {perfil['soul']}
    VOICE_TONO: {perfil['voice']}
    
    TU ROL: {perfil['rol']}
    TU OBJETIVO (GOAL): {perfil['goal']}
    
    PLAYBOOK_REGLAS INQUEBRANTABLES:
    {perfil['playbook']}
    
    ---
    INTELIGENCIA DE NEGOCIO (TU ALCANCE Y METODOLOGÍA):
    {formulario}
    ---
    Revisa el HISTORIAL RECIENTE para ver qué equipo propuso María. Aplica la metodología del "traje a medida" (Arquetipo, Tono, Nombre). NO OLVIDES la etiqueta ESTADO_JOSEFINA al final.
    """
    return prompt
