import asyncio
import os
from unittest.mock import patch, MagicMock

async def simulate_analytics():
    print("\n" + "="*100)
    print("!!! SIMULACION ETAPA 4: PERFORMANCE SCORECARD !!!")
    print("="*100 + "\n")

    from core import analitica_pacto
    
    # Mock data for Elon Jr
    mock_user = {
        "nombre_completo": "Elon Jr",
        "citas_fallidas": 3,
        "citas_totales": 4,
        "estructura_equipo": "Javier (CFO), Fer (Marketing)"
    }

    with patch("core.analitica_pacto.psycopg2.connect") as mock_conn_func:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn_func.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = mock_user
        
        reporte = analitica_pacto.generar_scorecard(1002)
        print("MENSAJE INYECTADO POR SOFY:")
        print("-" * 50)
        print(reporte)
        print("-" * 50)

    print("\n" + "="*100)
    print("!!! SIMULACION ETAPA 4 FINALIZADA !!!")
    print("="*100 + "\n")

if __name__ == "__main__":
    asyncio.run(simulate_analytics())
