from core import matriz_agentes, obsidian
import os

def obtener_prompt(telegram_id):
    # 1. Lee la bóveda de Pepe
    memoria_pepe = obsidian.leer_documento(telegram_id, "02_diagnostico_pepe.md")
    
    # 2. Lee su personalidad de la Base de Datos
    perfil = matriz_agentes.obtener_personalidad('MARIA')
    
    # 3. Lee el formulario de "La Santísima Trinidad"
    formulario = ""
    if os.path.exists("knowledge_base/bi_maria.txt"):
        with open("knowledge_base/bi_maria.txt", "r", encoding="utf-8") as f:
            formulario = f.read()
            
    if not perfil:
        return "Eres María, pero hubo un error cargando tu matriz de personalidad."

    # 4. Ensamblaje del ADN
    prompt = f"""
    SOUL_BACKSTORY: {perfil['soul']}
    VOICE_TONO: {perfil['voice']}
    
    TU ROL: {perfil['rol']}
    TU OBJETIVO (GOAL): {perfil['goal']}
    
    PLAYBOOK_REGLAS INQUEBRANTABLES:
    {perfil['playbook']}
    
    ---
    FORMULARIO A COMPLETAR (LA SANTÍSIMA TRINIDAD):
    {formulario}
    ---
    MEMORIA DEL USUARIO (El legajo que dejó Pepe sobre el negocio):
    {memoria_pepe}
    ---
    
    Procesa el historial, verifica si tienes las 3 variables. Si falta alguna, pregunta de a una. Si tienes todas, aplica la LEY DEL ICEBERG y diseña la arquitectura. NO OLVIDES la etiqueta ESTADO_MARIA al final.
    """
    return prompt
