import asyncio
import os
import time
from datetime import datetime, timedelta

async def simulate_watchdog():
    print("\n" + "="*100)
    print("!!! SIMULACION ETAPA 3: WATCHDOG 'KILL AND RECOVERY' !!!")
    print("="*100 + "\n")

    heartbeat_file = "core/fausto_heartbeat.txt"
    if os.path.exists(heartbeat_file): os.remove(heartbeat_file)
    
    print("1. El Daemon de Fausto escribe su latido...")
    # Simular la escritura de Fausto
    now = datetime.now()
    with open(heartbeat_file, "w") as f:
        f.write(str(now))
    
    from core import watchdog_fausto
    status, msg = watchdog_fausto.check_fausto_health()
    print(f"Estado inicial: {status} ({msg})")

    print("\n2. MATAMOS al proceso Fausto (simulando desincronizacion)...")
    # Ponemos un latido de hace 5 minutos
    old_beat = datetime.now() - timedelta(minutes=5)
    with open(heartbeat_file, "w") as f:
        f.write(str(old_beat))
    
    status, msg = watchdog_fausto.check_fausto_health()
    if not status:
        print(f"ALERTA ROJA: Watchdog detecto muerte cerebral! ({msg})")
        print("SISTEMA: Jero ha sido notificado para reanimar el proceso.")
    else:
        print("FAIL: Watchdog no detecto el fallo.")

    print("\n" + "="*100)
    print("!!! SIMULACION ETAPA 3 FINALIZADA !!!")
    print("="*100 + "\n")

if __name__ == "__main__":
    asyncio.run(simulate_watchdog())
