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
