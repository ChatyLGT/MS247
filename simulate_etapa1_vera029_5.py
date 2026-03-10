import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, time, timedelta

async def simulate_etapa1_fatiga():
    print("\n" + "="*100)
    print("!!! SIMULACION ETAPA 1: TESTEO CONDUCTUAL Y FATIGA (48HS) !!!")
    print("="*100 + "\n")

    from core import motor_fausto
    
    # Mocks
    mock_bot_instance = AsyncMock()
    
    with patch("core.motor_fausto.psycopg2.connect") as mock_conn_func, \
         patch("core.motor_fausto.bot", mock_bot_instance):
        
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn_func.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        
        # Scenario data
        user_base = {
            "id": 2, "telegram_id": 1002, "nombre_completo": "Elon Jr",
            "rubro": "Agencia Marketing", "dolor_principal": "desorden",
            "dias_compromiso": "Martes,Miercoles", "hora_inicio": time(9, 0),
            "ultimo_acceso": datetime.now() - timedelta(days=2),
            "estado_onboarding": "OPERACION_CONTINUA",
            "estructura_equipo": "Maker"
        }
        
        # SIMULAR 48 HORAS DE DESERCION (4 pokes)
        pokes = ["Poking 1 (Normal)", "Poking 2 (Normal)", "Poking 3 (Decepcionado)", "Poking 4 (Silencio)"]
        
        for i in range(4):
            counter = i
            print(f"\n--- HORA {9 + i}:00 (INTENTO {i+1}) ---")
            
            # Update user data for this turn
            user_data = user_base.copy()
            user_data["poking_counter"] = counter
            mock_cur.fetchall.return_value = [user_data]
            mock_cur.fetchone.return_value = None # No bunker
            
            # Force Tuesday/Wednesday
            fixed_now = datetime.now().replace(hour=10, minute=0) # 10:00 is > 09:15
            with patch("core.motor_fausto.datetime") as mock_date:
                mock_date.now.return_value = fixed_now
                mock_date.combine = datetime.combine
                mock_date.strftime = MagicMock(return_value='Martes')
                
                await motor_fausto.revisar_pacto_desercion(manual_now=fixed_now)

            if i < 3:
                if mock_bot_instance.send_message.called:
                    msg = mock_bot_instance.send_message.call_args[1].get('text', '')
                    print(f"FAUSTO SENT: {msg}")
                    mock_bot_instance.send_message.reset_mock()
            else:
                if not mock_bot_instance.send_message.called:
                    print("DONE: Fausto entro en modo SILENCIO absoluto tras 3 strikes.")
                else:
                    print("FAIL: Fausto siguio haciendo spam.")

    print("\n" + "="*100)
    print("!!! SIMULACION ETAPA 1 FINALIZADA !!!")
    print("="*100 + "\n")

if __name__ == "__main__":
    asyncio.run(simulate_etapa1_fatiga())
