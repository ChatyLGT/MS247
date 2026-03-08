from core import matriz_agentes, obsidian
import os

def obtener_prompt(telegram_id):
    # 1. Lee la bóveda de Pepe
    memoria_pepe = obsidian.leer_documento(telegram_id, "02_diagnostico_pepe.md")
    
    # 2. Compila el cerebro modular de María
    base_path = "agentes/fase1_onboarding/maria"
    alma_compilada = ""
    modulos = ["identity.md", "voice.md", "playbook.md"]
    for modulo in modulos:
        path = os.path.join(base_path, modulo)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                alma_compilada += f"\n\n### MODULO: {modulo.upper()} ###\n{f.read()}"
    
    if not alma_compilada:
        return "Eres María, pero hubo un error cargando tu matriz de personalidad."

    # 3. Ensamblaje del ADN
    prompt = f"""{alma_compilada}
    
    ---
    MEMORIA DEL USUARIO (El diagnóstico de Pepe sobre el negocio a estructurar):
    {memoria_pepe}
    ---
    
    Procesa el historial, verifica cómo puedes proponer una Arquitectura de Agentes de IA basada en el Dolor de este negocio. Explícale al usuario la propuesta de Agentes IA (Ej: Agente de Ventas, Agente de Marketing) y pídele validación.
    NO des consejos operativos como cambiar menús o recortar finanzas. Habla ÚNICAMENTE de instalar estructuras de Inteligencia Artificial para delegar.
    Si el usuario lo acepta con un "sí", "estoy de acuerdo", "adelante" o "ok", NO OLVIDES poner la etiqueta final: ESTADO_MARIA="Aprobado"
    """
    return prompt
