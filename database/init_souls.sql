CREATE TABLE IF NOT EXISTS agentes_personalidad (
    id_agente VARCHAR(50) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    rol_crewai VARCHAR(255) NOT NULL,
    objetivo_goal TEXT NOT NULL,
    soul_backstory TEXT NOT NULL,
    playbook_reglas TEXT NOT NULL,
    voice_tono TEXT NOT NULL
);

ALTER TABLE agentes_personalidad OWNER TO bot_master;
