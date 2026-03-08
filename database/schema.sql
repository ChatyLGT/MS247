-- Habilitar extensión pgvector para embeddings
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    nombre_completo VARCHAR(255),
    language_code VARCHAR(10),
    telefono_whatsapp VARCHAR(50),
    email VARCHAR(255),
    edad INTEGER,
    status_legal BOOLEAN DEFAULT FALSE,
    estado_onboarding VARCHAR(100) DEFAULT 'NUEVO',
    historial_reciente JSONB DEFAULT '[]'::jsonb,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tanque_gasolina NUMERIC(5,2) DEFAULT 100.00,
    tier_suscripcion VARCHAR(50) DEFAULT 'TRIAL'
);

CREATE TABLE IF NOT EXISTS adn_negocios (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE UNIQUE,
    nombre_empresa VARCHAR(255),
    rubro TEXT,
    dolor_principal TEXT,
    resumen_pepe TEXT,
    estructura_equipo TEXT,
    personalidad_agentes TEXT,
    rutinas_trabajo TEXT
);

CREATE TABLE IF NOT EXISTS memoria_vectorial (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    agente_emisor VARCHAR(100),
    contenido_texto TEXT,
    vector_embedding vector(768),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS proyectos_wbs (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    fase VARCHAR(100),
    descripcion TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tareas_wbs (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER REFERENCES proyectos_wbs(id) ON DELETE CASCADE,
    descripcion_tarea TEXT,
    estado VARCHAR(50) DEFAULT 'PENDIENTE',
    fecha_limite TIMESTAMP,
    fecha_completada TIMESTAMP
);

-- La Bóveda estilo Obsidian (Archivos Markdown Virtuales)
CREATE TABLE IF NOT EXISTS boveda_obsidian (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    nombre_documento VARCHAR(255) NOT NULL,
    contenido_md TEXT DEFAULT '',
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (telegram_id, nombre_documento)
);

-- El Rejection Log (Memoria de correcciones y evolución)
CREATE TABLE IF NOT EXISTS feedback_rechazos (
    id_rechazo SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    agente_involucrado VARCHAR(50) NOT NULL,
    tarea_original TEXT,
    motivo_rechazo TEXT NOT NULL,
    regla_aprendida TEXT NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sesiones_andrea (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    fecha_hora TIMESTAMP,
    recordatorio_30m_enviado BOOLEAN DEFAULT FALSE,
    recordatorio_inicio_enviado BOOLEAN DEFAULT FALSE,
    estado VARCHAR(50) DEFAULT 'PENDIENTE'
);

CREATE TABLE IF NOT EXISTS historial_clinico_encriptado (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    rol VARCHAR(50) NOT NULL,
    contenido TEXT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

