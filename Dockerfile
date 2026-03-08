# Usamos una imagen de Python moderna y ligera
FROM python:3.11-slim

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Configurar directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema operativo (necesarias para psycopg2, PyMuPDF, etc.)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiamos requerimientos (si existe) e instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del ecosistema
COPY . .

# Dar permisos de ejecución al entrypoint
RUN chmod +x scripts/start.sh

# Se establece el script maestro de arranque como Entrypoint
ENTRYPOINT ["./scripts/start.sh"]
