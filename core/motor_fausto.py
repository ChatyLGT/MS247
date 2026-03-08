import os, psycopg2, asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
bot = Bot(token=TOKEN)

async def revisar_citas_andrea():
    print("🕰️ [FAUSTO WORKER] Revisando citas de Andrea...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) if hasattr(psycopg2.extras, "RealDictCursor") else conn.cursor()
    
    now = datetime.now()
    t_30m = now + timedelta(minutes=30)

    try:
        # 1. Buscar recordatorios de 30 minutos
        cur.execute("SELECT * FROM sesiones_andrea WHERE recordatorio_30m_enviado = FALSE AND fecha_hora <= %s AND fecha_hora > %s", (t_30m, now))
        citas_30 = cur.fetchall()
        for cita in citas_30:
            msg = "🚨 <b>Recordatorio de Fausto:</b> Gunnar, su sesión con la Dra. Andrea comienza en 30 minutos. Prepare su entorno."
            await bot.send_message(chat_id=cita[1], text=msg, parse_mode="HTML")
            cur.execute("UPDATE sesiones_andrea SET recordatorio_30m_enviado = TRUE WHERE id = %s", (cita[0],))
        
        # 2. Buscar recordatorios de INICIO
        cur.execute("SELECT * FROM sesiones_andrea WHERE recordatorio_inicio_enviado = FALSE AND fecha_hora <= %s", (now,))
        citas_ya = cur.fetchall()
        for cita in citas_ya:
            msg = "🩺 <b>Dra. Andrea:</b> Estoy lista en la Sala Blindada. Cuando guste entrar, envíeme un mensaje."
            await bot.send_message(chat_id=cita[1], text=msg, parse_mode="HTML")
            cur.execute("UPDATE sesiones_andrea SET recordatorio_inicio_enviado = TRUE, estado = 'EN_CURSO' WHERE id = %s", (cita[0],))
        conn.commit()
    except Exception as e:
        print(f"Error revisando citas de Andrea: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

async def revisar_wbs_atrasado():
    print("🕰️ [FAUSTO WORKER] Revisando tareas WBS atrasadas...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) if hasattr(psycopg2.extras, "RealDictCursor") else conn.cursor()
    
    now = datetime.now()
    try:
        query = """
            SELECT t.id, t.descripcion_tarea, u.telegram_id 
            FROM tareas_wbs t
            JOIN proyectos_wbs p ON t.proyecto_id = p.id
            JOIN usuarios u ON p.usuario_id = u.id
            WHERE t.estado = 'PENDIENTE' AND t.fecha_limite < %s
        """
        cur.execute(query, (now,))
        tareas_atrasadas = cur.fetchall()
        
        for tarea in tareas_atrasadas:
            # We assume t.id is index 0, desc is index 1, telegram_id is index 2 if not RealDictCursor, but we use index safely if it's tuple
            tid = tarea['id'] if isinstance(tarea, dict) else tarea[0]
            desc = tarea['descripcion_tarea'] if isinstance(tarea, dict) else tarea[1]
            telegram_id = tarea['telegram_id'] if isinstance(tarea, dict) else tarea[2]
            
            msg = f"⚠️ <b>Alerta de Fausto (Asíncrono):</b> La tarea <i>'{desc}'</i> está atrasada según el WBS. ¿Necesitas que asigne a alguien del equipo para destrabarla?"
            await bot.send_message(chat_id=telegram_id, text=msg, parse_mode="HTML")
            # Para no spammear infinitamente, marcamos como NOTIFICADA o la movemos de estado.
            cur.execute("UPDATE tareas_wbs SET estado = 'ATRASADA_NOTIFICADA' WHERE id = %s", (tid,))
        conn.commit()
    except Exception as e:
        print(f"Error revisando WBS: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(revisar_citas_andrea, 'interval', minutes=1)
    scheduler.add_job(revisar_wbs_atrasado, 'interval', minutes=5)
    scheduler.start()
    
    print("🚀 Motor Asíncrono de Fausto (APScheduler) iniciado.")
    # Keep the main async loop running
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
