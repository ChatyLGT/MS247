import os
from core import matriz_agentes

def obtener_prompt(telegram_id):
    perfil = matriz_agentes.obtener_personalidad('FAUSTO')
    if not perfil:
        return "Eres Fausto, pero hubo un error cargando tu matriz."
    
    formulario = ""
    if os.path.exists("knowledge_base/bi_fausto.txt"):
        with open("knowledge_base/bi_fausto.txt", "r", encoding="utf-8") as f:
            formulario = f.read()
            
    prompt = f"""
    SOUL_BACKSTORY: {perfil['soul']}
    VOICE_TONO: {perfil['voice']}
    
    TU ROL: {perfil['rol']}
    TU OBJETIVO (GOAL): {perfil['goal']}
    
    PLAYBOOK_REGLAS INQUEBRANTABLES:
    {perfil['playbook']}
    
    ---
    INTELIGENCIA DE NEGOCIO (DOCTRINA HEROSUITE Y AGENDA):
    {formulario}
    ---
    Revisa el HISTORIAL RECIENTE para entender el equipo. Diseña el Roadmap de Transformación Digital (3 fases) y coordina la agenda de seguimiento. NO OLVIDES la etiqueta ESTADO_FAUSTO al final.
    """
    return prompt
