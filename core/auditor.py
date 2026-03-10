import os, glob
from datetime import datetime

LOG_DIR = "logs_sesiones"

def _obtener_archivo_actual(telegram_id):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    # Busca todos los logs del usuario y agarra el más reciente
    archivos = glob.glob(os.path.join(LOG_DIR, f"sesion_{telegram_id}_*.txt"))
    if archivos:
        return max(archivos, key=os.path.getctime)
    else:
        return iniciar_sesion(telegram_id)

def iniciar_sesion(telegram_id):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    fecha_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_archivo = os.path.join(LOG_DIR, f"sesion_{telegram_id}_{fecha_str}.txt")
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        f.write(f"=== INICIO DE CAJA NEGRA | USUARIO: {telegram_id} | {fecha_str} ===\n\n")
    print(f"Caja Negra creada: {nombre_archivo}")
    return nombre_archivo

def registrar_evento(telegram_id, actor, texto):
    archivo = _obtener_archivo_actual(telegram_id)
    timestamp = datetime.now().strftime("%H:%M:%S")
    entrada = f"[{timestamp}] {actor}:\n{texto}\n{'-'*50}\n"
    try:
        with open(archivo, "a", encoding="utf-8") as f:
            f.write(entrada)
    except Exception as e:
        print(f"Error escribiendo en Caja Negra: {e}")
