import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, time, timedelta

# --- SIMULATION ---
async def simulate_fausto_poking():
    print("\n" + "!"*100)
    print("!!! INICIANDO SIMULACION VERA-029: EL ACOSO DE FAUSTO !!!")
    print("!"*100 + "\n")

    from core import motor_fausto
    
    # Parcheamos dependencias
    mock_bot_instance = AsyncMock()
    
    with patch("core.motor_fausto.psycopg2.connect") as mock_conn_func, \
         patch("core.motor_fausto.bot", mock_bot_instance), \
         patch("core.motor_fausto.alertar_con_soul", AsyncMock(return_value="Elon Jr, son las 09:20. El marketing no descansa y tu desorden total tampoco. ¿Vienes o cerramos?")) as mock_soul:
        
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn_func.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        
        # Simular resultado de la query de usuarios
        mock_cur.fetchall.return_value = [
            {
                "id": 2, "telegram_id": 1002, "nombre_completo": "Elon Jr",
                "rubro": "Marketing", "dolor_principal": "desorden total",
                "dias_compromiso": "Martes,Jueves", "hora_inicio": time(9, 0),
                "ultimo_acceso": datetime.now() - timedelta(days=1),
                "estado_onboarding": "OPERACION_CONTINUA"
            }
        ]
        
        # Simular búnker libre
        mock_cur.fetchone.return_value = None 

        fixed_now = datetime.now().replace(hour=9, minute=20) # 09:20
        # No vamos a mockear datetime, vamos a pasarle el manual_now directamente al worker
        
        print(f"DEBUG: Simulando Hora {fixed_now.strftime('%H:%M')} en 'Tuesday' (forzado).")
        
        # El worker usa .strftime('%A') para detectar el día. 
        # Si hoy no es Martes, el test fallará a menos que mockeemos strftime o pasemos un Martes real.
        # Busquemos un Martes real cercano para fixed_now
        while fixed_now.strftime('%A') != 'Tuesday':
            fixed_now += timedelta(days=1)
        
        print(f"DEBUG: Fecha real de test: {fixed_now.strftime('%Y-%m-%d %H:%M:%S')} ({fixed_now.strftime('%A')})")
        
        await motor_fausto.revisar_pacto_desercion(manual_now=fixed_now)

        # Verificaciones
        if mock_bot_instance.send_message.called:
            print("SUCCESS: Fausto envio el mensaje proactivo.")
            print(f"LOG FAUSTO: {mock_bot_instance.send_message.call_args[1].get('text', 'N/A')}")
        else:
            print("FAIL: Fausto no se desperto.")

        # Test Búnker Andrea (Intercepción)
        print("\n--- TEST: Intercepcion de Andrea (Bunquer Sagrado) ---")
        mock_bot_instance.send_message.reset_mock()
        mock_cur.fetchone.return_value = [1] # Simular sesión activa en Andrea
        
        await motor_fausto.revisar_pacto_desercion(manual_now=fixed_now)
        
        if not mock_bot_instance.send_message.called:
            print("SUCCESS: Fausto respeto el bunquer de Andrea y callo.")
        else:
            print("FAIL: Fausto violo el bunquer de Andrea.")

    print("\n" + "!"*100)
    print("!!! SIMULACION VERA-029 FINALIZADA !!!")
    print("!"*100 + "\n")

if __name__ == "__main__":
    asyncio.run(simulate_fausto_poking())
