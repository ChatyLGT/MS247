import os, psycopg2, psycopg2.extras, asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
bot = Bot(token=TOKEN)

from core.gemini_multimodal import procesar_texto_puro

async def alertar_con_soul(contenido_alerta, telegram_id):
    try:
        with open("agentes/fase2_ejecucion/fausto/soul.md", "r") as f:
            soul = f.read()
    except:
        soul = "Eres Fausto, un controller serio."
        
    prompt = f"{soul}\n\nREDACTA UNA ALERTA CORTA (Máximo 2 líneas) PARA ESTA SITUACIÓN:\n{contenido_alerta}"
    res = await procesar_texto_puro(prompt, "Generar Alerta", telegram_id=telegram_id)
    return res

async def revisar_citas_andrea():
    print("🕰️ [FAUSTO WORKER] Revisando citas de Andrea...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        now = datetime.now()
        t_30m = now + timedelta(minutes=30)

        # 1. Buscar recordatorios de 30 minutos
        cur.execute("SELECT * FROM sesiones_andrea WHERE recordatorio_30m_enviado = FALSE AND fecha_hora <= %s AND fecha_hora > %s", (t_30m, now))
        citas_30 = cur.fetchall()
        for cita in citas_30:
            msg_soul = await alertar_con_soul(f"Sesión con la Dra. Andrea en 30 minutos para el usuario.", cita['telegram_id'])
            await bot.send_message(chat_id=cita['telegram_id'], text=f"🚨 <b>Fausto:</b> {msg_soul}", parse_mode="HTML")
            cur.execute("UPDATE sesiones_andrea SET recordatorio_30m_enviado = TRUE WHERE id = %s", (cita['id'],))
        
        # 2. Recordatorios de INICIO (Mantenemos el de Andrea directo por ser su voz)
        cur.execute("SELECT * FROM sesiones_andrea WHERE recordatorio_inicio_enviado = FALSE AND fecha_hora <= %s", (now,))
        citas_ya = cur.fetchall()
        for cita in citas_ya:
            msg = "🩺 <b>Dra. Andrea:</b> Estoy lista en la Sala Blindada. Cuando guste entrar, envíeme un mensaje."
            await bot.send_message(chat_id=cita['telegram_id'], text=msg, parse_mode="HTML")
            cur.execute("UPDATE sesiones_andrea SET recordatorio_inicio_enviado = TRUE, estado = 'EN_CURSO' WHERE id = %s", (cita['id'],))
        conn.commit()
    except Exception as e:
        print(f"Error revisando citas de Andrea: {e}")
    finally:
        if 'conn' in locals(): conn.close()

async def revisar_wbs_atrasado():
    print("🕰️ [FAUSTO WORKER] Revisando tareas WBS atrasadas...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        now = datetime.now()
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
            msg_soul = await alertar_con_soul(f"La tarea '{tarea['descripcion_tarea']}' está atrasada en el WBS.", tarea['telegram_id'])
            await bot.send_message(chat_id=tarea['telegram_id'], text=f"⚠️ <b>Fausto:</b> {msg_soul}", parse_mode="HTML")
            cur.execute("UPDATE tareas_wbs SET estado = 'ATRASADA_NOTIFICADA' WHERE id = %s", (tarea['id'],))
        conn.commit()
    except Exception as e:
        print(f"Error revisando WBS: {e}")
    finally:
        if 'conn' in locals(): conn.close()

async def db_heartbeat():
    """Chequeo de salud de la base de datos (Doctrina 2026)"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        print("💓 [HEARTBEAT] Base de Datos Saludable.")
    except Exception as e:
        print(f"💔 [HEARTBEAT] ERROR CRÍTICO DB: {e}")
        # Aquí podrías mandar un Telegram al ADMIN_ID si estuviera configurado

async def extraer_hechos_cognee(mensaje):
    """Extrae hechos clave (Cognee Pattern) de un mensaje."""
    schema_hechos = {
        "type": "OBJECT",
        "properties": {
            "hechos": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "entidad": {"type": "STRING", "description": "Sujeto u Objeto (ej. 'Empresa', 'Gunnar', 'Proyecto X')"},
                        "relacion": {"type": "STRING", "description": "Acción o atributo (ej. 'tiene_problema', 'dueño_de', 'estado')"},
                        "valor": {"type": "STRING", "description": "Valor del atributo"}
                    },
                    "required": ["entidad", "relacion", "valor"]
                }
            }
        },
        "required": ["hechos"]
    }
    
    prompt = """Analiza el siguiente mensaje de una consultoría de negocios y extrae HECHOS CLAVE en formato relacional (Grafo de Conocimiento).
Excluye saludos o charlas triviales. Concéntrate en: Dolores, Estructuras, Nombres, Decisiones y Estados de Proyecto.

MENSAJE:
"""
    import json
    res_json = await procesar_texto_puro(
        prompt, 
        mensaje['contenido'], 
        response_schema=schema_hechos
    )
    try:
        data = json.loads(res_json)
        for hecho in data.get("hechos", []):
            db.guardar_hecho_clave(mensaje['telegram_id'], hecho['entidad'], hecho['relacion'], hecho['valor'])
        return True
    except Exception as e:
        print(f"Error extrayendo hechos: {e}")
        return False

async def revisar_cola_cognee():
    print("🕰️ [FAUSTO WORKER] Procesando cola Cognee (Memoria Transaccional)...")
    pendientes = db.obtener_pendientes_cognee(limit=5)
    for msg in pendientes:
        print(f"🧠 Analizando mensaje ID {msg['id']} para usuario {msg['telegram_id']}...")
        success = await extraer_hechos_cognee(msg)
        if success:
            db.marcar_procesado_cognee(msg['id'])

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(revisar_citas_andrea, 'interval', minutes=1)
    scheduler.add_job(revisar_wbs_atrasado, 'interval', minutes=5)
    scheduler.add_job(revisar_cola_cognee, 'interval', minutes=2)
    scheduler.add_job(db_heartbeat, 'interval', minutes=10)
    scheduler.start()
    
    print("🚀 Motor Asíncrono de Fausto (APScheduler) iniciado con Cognee Worker.")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
