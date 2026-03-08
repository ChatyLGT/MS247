#!/bin/bash
set -e

echo "======================================"
echo "🚀 INICIANDO PROTOCOLO DE ENCENDIDO MS247"
echo "======================================"

echo "[1/4] ⏳ Esperando a que PostgreSQL esté aceptando conexiones..."
# pg_isready usa la variable DATABASE_URL inyectada por Docker Compose
until pg_isready -d "$DATABASE_URL"; do
  echo "La base de datos no está lista. Reintentando en 2 segundos..."
  sleep 2
done
echo "✅ Base de datos operativa."

echo "[2/4] 🛠️ Inicializando esquema de base de datos..."
if [ -f "database/schema.sql" ]; then
    psql "$DATABASE_URL" -f database/schema.sql
    echo "✅ Esquema validado."
else
    echo "⚠️ ADVERTENCIA: No se encontró database/schema.sql"
fi

echo "[3/4] 🧠 Inyectando semilla documental (RAG PGVector)..."
if [ -f "scripts/seed_knowledge.py" ]; then
    # Añadir el directorio actual al PYTHONPATH para que los scripts encuentren el módulo 'core'
    export PYTHONPATH=$PWD
    python scripts/seed_knowledge.py
    echo "✅ Conocimiento ingerido."
else
    echo "⚠️ ADVERTENCIA: No se encontró scripts/seed_knowledge.py"
fi

echo "[4/4] 🚀 MISION CRITICA: Iniciando motores..."
# Iniciamos el motor asíncrono de tareas programadas (Fausto) en background
if [ -f "core/motor_fausto.py" ]; then
    echo "Activando Motor Asíncrono (Fausto)..."
    python core/motor_fausto.py &
fi

# El proceso principal que mantiene el contenedor vivo es el Webhook/Polling (Sofy)
if [ -f "telegram_bridge.py" ]; then
    echo "Activando Puente de Telegram (Sofy)..."
    exec python telegram_bridge.py
else
    echo "❌ ERROR: No se encontró telegram_bridge.py. El contenedor se detendrá."
    exit 1
fi
