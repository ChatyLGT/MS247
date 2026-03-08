import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST", "localhost")

try:
    if db_url:
        conn = psycopg2.connect(db_url)
    else:
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
    
    cur = conn.cursor()
    cur.execute("ALTER TABLE adn_negocios ADD COLUMN notas_pepe TEXT DEFAULT '';")
    conn.commit()
    print("✅ CIRUGÍA EXITOSA: La memoria a largo plazo de Pepe ('notas_pepe') está instalada.")
except psycopg2.errors.DuplicateColumn:
    print("⚠️ La columna 'notas_pepe' ya existía. Todo en orden.")
except Exception as e:
    print(f"❌ Error conectando a la BD: {e}")
    print("👉 SOLUCIÓN MANUAL: Abre tu gestor de base de datos SQL y corre este comando:")
    print("ALTER TABLE adn_negocios ADD COLUMN notas_pepe TEXT;")
finally:
    if 'conn' in locals(): conn.close()
