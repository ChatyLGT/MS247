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
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tanque_gasolina NUMERIC(5,2) DEFAULT 100.00,
    tier_suscripcion VARCHAR(50) DEFAULT 'TRIAL'
);

CREATE TABLE IF NOT EXISTS adn_negocios (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE UNIQUE,
    nombre_empresa VARCHAR(255),
    modelo_negocio TEXT,
    tipo_ayuda_esperada TEXT,
    liderazgo_rutinas TEXT
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
