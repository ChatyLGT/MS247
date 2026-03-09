import os, psycopg2, json
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def obtener_usuario(telegram_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM usuarios WHERE telegram_id = %s;", (telegram_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def crear_usuario(telegram_id, username=None, nombre_completo=None, language_code=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO usuarios (telegram_id, username, nombre_completo, language_code, estado_onboarding) 
        VALUES (%s, %s, %s, %s, 'NUEVO') 
        ON CONFLICT (telegram_id) DO UPDATE SET
            username = EXCLUDED.username,
            nombre_completo = EXCLUDED.nombre_completo,
            language_code = EXCLUDED.language_code;
    """, (telegram_id, username, nombre_completo, language_code))
    conn.commit()
    cur.close()
    conn.close()

def guardar_memoria_hilo(telegram_id, rol, contenido, es_andrea=False):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT estado_onboarding FROM usuarios WHERE telegram_id = %s", (telegram_id,))
    row = cur.fetchone()
    estado = row[0] if row else ""
    
    if es_andrea or estado == "EMERGENCY_COACHING" or "ANDREA" in rol.upper():
        print(f"🔒 LOG DB: [SALA BLINDADA] Guardando secreto de Andrea para User {telegram_id}")
        cur.execute("INSERT INTO historial_clinico_encriptado (telegram_id, rol, contenido) VALUES (%s, %s, %s)", (telegram_id, rol, contenido))
    else:
        print(f"📊 LOG DB: [MEMORIA GENERAL] Guardando interacción de negocio para User {telegram_id}")
        cur.execute("SELECT historial_reciente FROM usuarios WHERE telegram_id = %s", (telegram_id,))
        row = cur.fetchone()
        historial = row[0] if row and row[0] else []
        historial.append({"rol": rol, "txt": contenido})
        historial = historial[-10:]
        cur.execute("UPDATE usuarios SET historial_reciente = %s WHERE telegram_id = %s", (json.dumps(historial), telegram_id))
    conn.commit()
    cur.close()
    conn.close()

def obtener_memoria_andrea(telegram_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # Obtenemos los últimos 15 mensajes de la Sala Blindada
    cur.execute("SELECT rol, contenido as txt FROM historial_clinico_encriptado WHERE telegram_id = %s ORDER BY fecha_creacion DESC LIMIT 15;", (telegram_id,))
    res = cur.fetchall()
    cur.close()
    conn.close()
    return list(reversed(res))

def obtener_adn_completo(telegram_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT u.nombre_completo, u.email, u.estado_onboarding, u.historial_reciente,
                an.nombre_empresa, an.rubro, an.dolor_principal, an.resumen_pepe,
                an.estructura_equipo, an.personalidad_agentes, an.rutinas_trabajo
        FROM usuarios u
        LEFT JOIN adn_negocios an ON u.id = an.usuario_id
        WHERE u.telegram_id = %s;
    """
    cur.execute(query, (telegram_id,))
    res = cur.fetchone()
    cur.close()
    conn.close()
    return res or {}

def actualizar_adn(telegram_id, campo, valor):
    conn = get_connection()
    cur = conn.cursor()
    query = f"UPDATE adn_negocios SET {campo} = %s WHERE usuario_id = (SELECT id FROM usuarios WHERE telegram_id = %s);"
    cur.execute(query, (valor, telegram_id))
    conn.commit()
    cur.close()
    conn.close()

def inicializar_adn(telegram_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO adn_negocios (usuario_id) SELECT id FROM usuarios WHERE telegram_id = %s ON CONFLICT DO NOTHING;", (telegram_id,))
    conn.commit()
    cur.close()
    conn.close()

def actualizar_campo_usuario(telegram_id, campo, valor):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE usuarios SET {campo} = %s WHERE telegram_id = %s;", (valor, telegram_id))
    conn.commit()
    cur.close()
    conn.close()

def obtener_contexto_negocio(telegram_id):
    adn = obtener_adn_completo(telegram_id)
    return adn.get('nombre_empresa', "")

def restar_tokens_gasolina(telegram_id, cantidad):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE usuarios SET tanque_gasolina = tanque_gasolina - %s WHERE telegram_id = %s", (cantidad, telegram_id))
        conn.commit()
        cur.close()
        conn.close()
        print(f"⛽ [TELEMETRÍA] {cantidad} tokens descontados del usuario {telegram_id}.")
    except Exception as e:
        print(f"⚠️ Error descontando tokens: {e}")

def borrar_usuario(telegram_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM boveda_obsidian WHERE telegram_id = %s", (telegram_id,))
    cur.execute("DELETE FROM feedback_rechazos WHERE telegram_id = %s", (telegram_id,))
    cur.execute("DELETE FROM adn_negocios WHERE usuario_id = (SELECT id FROM usuarios WHERE telegram_id = %s)", (telegram_id,))
    cur.execute("DELETE FROM usuarios WHERE telegram_id = %s", (telegram_id,))
    conn.commit()
    cur.close()
    conn.close()

def es_peticion_duplicada(update_id):
    """Verifica si un update_id ya fue procesado."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM peticiones_procesadas WHERE update_id = %s", (update_id,))
    res = cur.fetchone()
    cur.close()
    conn.close()
    return res is not None

def registrar_peticion_procesada(update_id):
    """Registra un update_id como procesado."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO peticiones_procesadas (update_id) VALUES (%s) ON CONFLICT DO NOTHING", (update_id,))
        conn.commit()
    except Exception as e:
        print(f"⚠️ Error registrando petición: {e}")
    finally:
        cur.close()
        conn.close()
