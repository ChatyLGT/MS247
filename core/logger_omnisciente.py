import logging, logging.handlers
import sys
import os
from datetime import datetime

# 1. Aseguramos la carpeta de logs
os.makedirs("logs", exist_ok=True)

# 2. Archivo ÚNICO por sesión (con marca de tiempo exacta)
timestamp_sesion = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = f"logs/sesion_omnisciente_{timestamp_sesion}.log"

# 3. Formato clínico y detallado
log_format = '%(asctime)s | %(levelname)s | [%(name)s] | %(message)s'

# 4. Configuración del núcleo de logging (Rotación de 10MB, conservando 3 backups)
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.handlers.RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=3, encoding='utf-8'),
        logging.StreamHandler(sys.stdout) # Salida a tu terminal
    ]
)

# 5. EL SILENCIADOR: Apagamos el ruido de red y librerías externas
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.ERROR) # Solo errores reales
logging.getLogger("apscheduler").setLevel(logging.WARNING) # Menos ruido de Fausto

def obtener_chismografo(nombre_modulo):
    """Devuelve un logger configurado para el módulo específico."""
    return logging.getLogger(nombre_modulo)


# --- INYECCIÓN DE OBSERVABILIDAD EXTREMA ---
import json
import time
from functools import wraps
import asyncio

def log_evento_crudo(nombre_modulo, mensaje, payload=None):
    """Registra un evento con un payload JSON formateado para máxima legibilidad."""
    log = logging.getLogger(nombre_modulo)
    if payload:
        try:
            payload_str = json.dumps(payload, indent=2, ensure_ascii=False)
            log.info(f"{mensaje} \n[PAYLOAD]:\n{payload_str}")
        except Exception:
            log.info(f"{mensaje} | [PAYLOAD CRUDO]: {payload}")
    else:
        log.info(mensaje)

def medir_tiempo(func):
    """Decorador para medir la latencia exacta de las operaciones (ej. LLMs)."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        inicio = time.perf_counter()
        resultado = await func(*args, **kwargs)
        fin = time.perf_counter()
        logging.getLogger(func.__module__).info(f"LATENCIA [{func.__name__}]: {fin - inicio:.4f} segundos.")
        return resultado

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        inicio = time.perf_counter()
        resultado = func(*args, **kwargs)
        fin = time.perf_counter()
        logging.getLogger(func.__module__).info(f"LATENCIA [{func.__name__}]: {fin - inicio:.4f} segundos.")
        return resultado

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
