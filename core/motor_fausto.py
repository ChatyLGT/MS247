import os, psycopg2, psycopg2.extras, asyncio
from datetime import datetime, timedelta, time
from dotenv import load_dotenv
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
bot = Bot(token=TOKEN)

from core.gemini_multimodal import procesar_texto_puro
from core import db

async def alertar_con_soul(contenido_alerta, telegram_id):
    try:
        with open("agentes/fase2_ejecucion/fausto/soul.md", "r") as f:
            soul = f.read()
    except:
        soul = "Eres Fausto, un controller serio."
    prompt = f"{soul}\n\nREDACTA UNA ALERTA CORTA (Maximo 2 lineas) PARA ESTA SITUACION:\n{contenido_alerta}"
    res = await procesar_texto_puro(prompt, "Generar Alerta", telegram_id=telegram_id)
    return res

async def revisar_citas_andrea():
    print("[FAUSTO WORKER] Revisando citas de Andrea...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        now = datetime.now()
        t_30m = now + timedelta(minutes=30)
        cur.execute("SELECT * FROM sesiones_andrea WHERE recordatorio_30m_enviado = FALSE AND fecha_hora <= %s AND fecha_hora > %s", (t_30m, now))
        citas_30 = cur.fetchall()
        for cita in citas_30:
            msg_soul = await alertar_con_soul(f"Sesion con la Dra. Andrea en 30 minutos.", cita['telegram_id'])
            await bot.send_message(chat_id=cita['telegram_id'], text=f"ALERTA: <b>Fausto:</b> {msg_soul}", parse_mode="HTML")
            cur.execute("UPDATE sesiones_andrea SET recordatorio_30m_enviado = TRUE WHERE id = %s", (cita['id'],))
        conn.commit()
    except Exception as e:
        print(f"Error citas Andrea: {e}")
    finally:
        if 'conn' in locals(): conn.close()

async def generar_mensaje_poking_especializado(niche, level, counter):
    """ETAPA 2: Catalogo de Rubros y Consecuencias Logicas"""
    import random
    
    consecuencias = {
        "Panaderia": "se te enfria el horno y la masa se sobreleuda",
        "Inmobiliaria": "el lead se va con la competencia y pierdes la exclusiva",
        "Marketing": "el algoritmo penaliza tu estancamiento creativo",
        "Clinica": "los pacientes se van sin turno y pierdes fidelidad",
        "Gimnasio": "las maquinas estan ociosas y el flujo de caja se detiene",
        "Default": "el mercado no espera a los que se quedan dormidos"
    }
    
    cons = consecuencias.get(niche, consecuencias["Default"])
    
    tonos = {
        0: "Normal", 1: "Normal", 2: "Normal",
        3: "Decepcionado y preocupado por tu falta de compromiso"
    }
    tono = tonos.get(counter, "Silencio")
    if tono == "Silencio": return None

    # Variantes por Nivel
    variantes = {
        "Consultivo": [
            f"Socio, tu estrategia para {niche} se desmorona. {cons}. ¿Retomamos?",
            f"El plan de hoy en {niche} esta en pausa. Recuerda que {cons}.",
            f"La Mesa Directiva espera. Sin tu direccion en {niche}, {cons}."
        ],
        "Maker": [
            f"Hay contenido de {niche} que no se esta redactando. {cons}. ¿Damos luz verde?",
            f"Tu equipo Maker esta parado. El desorden en {niche} crece y {cons}.",
            f"Si no entras ahora, el trabajo de {niche} se acumula y {cons}."
        ],
        "Autonomo": [
            f"Los sistemas autonomos de {niche} reportan inactividad humana. {cons}.",
            f"Revision de API en {niche} pendiente. El sistema esta ciego y {cons}.",
            f"Accountability check: {niche} necesita tu supervision de alto nivel o {cons}."
        ]
    }
    
    v_lista = variantes.get(level, variantes["Consultivo"])
    base_msg = random.choice(v_lista)

    prompt = f"Eres Fausto. Mejora este mensaje respetando el Tono '{tono}': '{base_msg}'.\n"
    prompt += "REGLA: Maximo 2 lineas. NO USES EMOJIS."
    
    return prompt

async def revisar_pacto_desercion(manual_now=None):
    from datetime import datetime as dt_class, time as t_class, timedelta as delta_class
    print("[FAUSTO WORKER] Revisando cumplimiento de Pactos de Sangre...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT u.id, u.telegram_id, u.nombre_completo, an.rubro, an.dolor_principal, 
                   an.dias_compromiso, an.hora_inicio, u.ultimo_acceso, u.estado_onboarding,
                   u.poking_counter, an.estructura_equipo
            FROM usuarios u 
            JOIN adn_negocios an ON u.id = an.usuario_id 
            WHERE u.estado_onboarding = 'OPERACION_CONTINUA'
        """
        cur.execute(query)
        usuarios = cur.fetchall()
        now = manual_now if manual_now else dt_class.now()
        hoy_str = now.strftime('%A') 
        dias_map = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miercoles', 'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sabado', 'Sunday': 'Domingo'}
        hoy_es = dias_map.get(hoy_str)
        
        for u in usuarios:
            tid = u['telegram_id']
            if u['estado_onboarding'] == 'EMERGENCY_COACHING': continue
            
            cur.execute("SELECT 1 FROM historial_clinico_encriptado WHERE telegram_id = %s AND fecha_creacion > %s", (tid, now - delta_class(hours=24)))
            if cur.fetchone(): continue
            
            mis_dias = u['dias_compromiso'] or ""
            if hoy_es not in mis_dias: continue
            
            h_pacto = u['hora_inicio']
            if not h_pacto: continue
            
            if isinstance(h_pacto, str):
                try: h_pacto = dt_class.strptime(h_pacto, "%H:%M:%S").time()
                except: h_pacto = dt_class.strptime(h_pacto, "%H:%M").time()
            
            pacto_hoy = dt_class.combine(now.date(), h_pacto)
            if now > (pacto_hoy + delta_class(minutes=15)):
                # Verificar si ya entro hoy
                ultimo = u['ultimo_acceso']
                if not ultimo or (isinstance(ultimo, dt_class) and ultimo.date() < now.date()):
                    # ETAPA 1: Fatiga e Ignorado
                    counter = u.get('poking_counter', 0)
                    
                    if counter >= 4:
                        print(f"INFO: Fausto en modo SILENCIO para {u['nombre_completo']} (Ignorado > 3 veces)")
                        continue
                        
                    print(f"ALERTA: Desercion detectada para {u['nombre_completo']} (Strike {counter+1})")
                    
                    # ETAPA 2: Poking Especializado
                    level = "Consultivo" # Default
                    if "Maker" in (u['estructura_equipo'] or ""): level = "Maker"
                    if "Autonomo" in (u['estructura_equipo'] or ""): level = "Autonomo"
                    
                    prompt_poke = await generar_mensaje_poking_especializado(u['rubro'], level, counter + 1)
                    if prompt_poke:
                        msg_soul = await procesar_texto_puro(prompt_poke, "Generar Poking", telegram_id=tid)
                        await bot.send_message(chat_id=tid, text=f"FAUSTO: {msg_soul}", parse_mode="HTML")
                        
                        # Incrementar counter y marcar cita fallida
                        cur.execute("UPDATE usuarios SET poking_counter = poking_counter + 1, citas_fallidas = citas_fallidas + 1, citas_totales = citas_totales + 1 WHERE id = %s", (u['id'],))
        conn.commit()
    except Exception as e:
        print(f"Error en worker de desercion: {type(e).__name__} - {e}")
    finally:
        if 'conn' in locals(): conn.close()

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(revisar_citas_andrea, 'interval', minutes=1)
    scheduler.add_job(revisar_pacto_desercion, 'interval', minutes=5)
    scheduler.start()
    print("Motor Asincrono de Fausto activo.")
    while True:
        # HEARTBEAT para Watchdog (Etapa 3)
        with open("core/fausto_heartbeat.txt", "w") as f:
            f.write(str(datetime.now()))
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
