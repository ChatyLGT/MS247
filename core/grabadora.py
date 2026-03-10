from datetime import datetime
import re
try:
    from core import auditor
except ImportError:
    auditor = None

AZUL, VERDE, AMARILLO, ROJO, CYAN, RESET = "\033[94m", "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[0m"

def _extraer_id(identidad):
    if not identidad: return None
    if isinstance(identidad, int): return identidad
    match = re.search(r'ID:(\d+)', str(identidad))
    return int(match.group(1)) if match else None

def log_terminal(tipo, usuario, detalle):
    """Pinta en terminal y graba en la Caja Negra"""
    hora = datetime.now().strftime("%H:%M:%S")
    id_user = _extraer_id(usuario)
    color_user = ROJO if "DESCONOCIDO" in str(usuario) else CYAN
    
    if any(x in tipo for x in ["COMANDO", "CALLBACK", "TYC"]): color_tipo = AMARILLO
    elif any(x in tipo for x in ["TEXTO", "WHATSAPP", "CONTACTO"]): color_tipo = AZUL
    elif any(x in tipo for x in ["IMAGEN", "AUDIO", "DOC", "VIDEO", "MUSICA"]): color_tipo = CYAN
    elif "SISTEMA" in tipo: color_tipo = ROJO
    else: color_tipo = RESET

    print(f"{color_tipo}[{hora}] (IN) {tipo} | User: {color_user}{usuario}{color_tipo} | {detalle}{RESET}")
    
    if auditor and id_user:
        auditor.registrar_evento(id_user, f"SISTEMA_{tipo}", detalle)

def log_bot_response(agente, respuesta, telegram_id=None):
    """Registra respuestas de agentes en verde y las graba"""
    hora = datetime.now().strftime("%H:%M:%S")
    limpio = re.sub(r'\[DATA:.*?\]', '', respuesta).strip()
    print(f"\n{VERDE}[{hora}] RESPONSE | Agente: {agente} | {limpio}{RESET}\n")
    
    if auditor and telegram_id:
        auditor.registrar_evento(telegram_id, f"IA_{agente}", limpio)

def log_forense(agente, raw_ia, telegram_id=None):
    """Graba el razonamiento 'espia' en la Caja Negra (Invisible en terminal)"""
    if auditor and telegram_id:
        auditor.registrar_evento(telegram_id, f"FORENSE_{agente}", raw_ia)
