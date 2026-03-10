import os
import time
from datetime import datetime
from core import db

def check_fausto_health():
    """Etapa 3: Watchdog para Fausto"""
    heartbeat_file = "core/fausto_heartbeat.txt"
    if not os.path.exists(heartbeat_file):
        return False, "Fail: No heartbeat file."
    
    with open(heartbeat_file, "r") as f:
        last_beat_str = f.read().strip()
    
    try:
        last_beat = datetime.strptime(last_beat_str, "%Y-%m-%d %H:%M:%S.%f")
        diff = (datetime.now() - last_beat).total_seconds()
        if diff > 180: # 3 minutos sin pulso
            return False, f"Desincronizacion: {diff} segundos."
    except:
        return False, "Corrupcion de latido."
        
    return True, "OK"

async def alertar_jero_fallo_fausto():
    print("WATCHDOG: Fausto esta muerto. Alertando a Jero...")
    # Aqui se enviaria un mensaje a los admins o log de sistema
    pass

if __name__ == "__main__":
    # Test local
    status, msg = check_fausto_health()
    print(f"Watchdog status: {status} ({msg})")
