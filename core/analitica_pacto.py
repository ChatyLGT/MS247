import psycopg2
import psycopg2.extras
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def generar_scorecard(telegram_id):
    """Etapa 4: Analitica de Pacto y Scorecard"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("SELECT u.nombre_completo, u.citas_fallidas, u.citas_totales, an.estructura_equipo FROM usuarios u JOIN adn_negocios an ON u.id = an.usuario_id WHERE u.telegram_id = %s", (telegram_id,))
        u = cur.fetchone()
        
        if not u: return "No hay datos para este socio."
        
        totales = u['citas_totales'] or 1
        fallidas = u['citas_fallidas'] or 0
        exitosas = totales - fallidas
        ratio = (exitosas / totales) * 100
        
        # Estimar ocio de agentes
        # Si un socio falla, sus agentes estan ociosos.
        ocio = (fallidas / totales) * 100
        
        # Contar agentes
        equipo = u['estructura_equipo'] or ""
        num_agentes = equipo.count(",") + 1 if equipo else 0
        
        reporte = (
            f"REPORTE DE MADUREZ OPERATIVA:\n"
            f"Tu nivel de compromiso esta semana fue del {ratio:.0f}%.\n"
            f"Fallaste en {fallidas} citas pactadas.\n"
            f"Tu equipo de {num_agentes} agentes estuvo ocioso el {ocio:.0f}% del tiempo pactado."
        )
        return reporte
        
    except Exception as e:
        return f"Error analitica: {e}"
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    # Test local
    print(generar_scorecard(1002))
