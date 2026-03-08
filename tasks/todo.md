# MS247 Architectural Dependencies Plan (V2.0)

## Fase 1 Completada
- [x] Mapear máquina de estados en `telegram_bridge.py`.
- [x] Validar que Jero bloquee el paso hasta que Bruno cierre la variable de WBS.
- [x] Refactorizar `core/router_jero.py` con `langgraph.graph.StateGraph`.
- [x] Crear el `Supervisor Node` para que lea de `adn_negocios`.
- [x] Asegurar que arme el `System Prompt` al vuelo basándose en los sockets de María y data de Josefina.
- [x] Refactorizar `core/motor_fausto.py` usando `APScheduler`.
- [x] Implementar un scheduler que lea `proyectos_wbs`.
- [x] Crear la tabla `proyectos_wbs` en `schema.sql`.
- [x] Modificar `db.guardar_memoria_hilo` para capturar la bandera `EMERGENCY_COACHING` y enviarlo a `historial_clinico_encriptado`.

## Fase 2 Completada
- [x] **Telemetría del Tanque de Gasolina:** Modificar `db.py` para abstraer la escritura asíncrona de consumo de tokens.
- [x] **Telemetría en LangGraph:** Implementar callback en `router_jero.py` (y en todos los agentes) para interceptar `total_tokens_used` y actualizar la tabla de tokens.
- [x] **RAG Desacoplado (Adapter):** Crear `core/rag_service.py` con interfaz abstracta que permita conmutar entre PGVector y NotebookLM vía variable de entorno.
- [x] **Action Space & Sandbox (Makers):** Habilitar Function Calling para los Sockets de Especialistas (Ana, Javier, Marce) usando la funcionalidad nativa de ejecución de código de Gemini (`{"code_execution": {}}`).
- [x] **Action Space & Sandbox (Makers):** Proporcionar entorno/sandbox interactivo para que Gemini ejecute actualizaciones en la tabla WBS independientemente (`ejecutar_agente_sandbox`).

## Fase 3: UX en Telegram, Resiliencia y Semilla de Conocimiento
- [x] **Manejo de Errores Global:** Refactorizar `telegram_bridge.py` con `try/except` global y mensajes empáticos de Sofy.
- [x] **Filtro de Contenido Soportado:** Interceptar stickers, GIFs y videos que sumen ruido innecesario, devolviendo fallback amigable.
- [x] **Procesamiento de Voz y Limpieza:** Capturar mensajes de voz/audio, procesarlos y **obligatoriamente** eliminar los archivos temporales de `/tmp/` dentro de un bloque `finally`.
- [x] **Semilla Documental:** Crear `scripts/seed_knowledge.py` usando `PyMuPDF` (prohibido PyPDF2) para preservar estructura de PDFs, generar embeddings e inyectarlos a `memoria_vectorial`.

## Fase 4: Empaquetado, Despliegue y Protocolo de Encendido
- [x] **Contenedorización Absoluta:** Crear `docker-compose.yml` (App + PostgreSQL con `pgvector` nativo).
- [x] **Contenedorización Absoluta:** Crear `Dockerfile` instalando dependencias de sistema y Python.
- [x] **Automatización de Arranque:** Crear `scripts/start.sh` que espere a que la base de datos esté lista con `pg_isready`.
- [x] **Automatización de Arranque:** Configurar `scripts/start.sh` para autoejecutar `schema.sql`.
- [x] **Automatización de Arranque:** Configurar `scripts/start.sh` para autoejecutar la Ingesta de RAG (`seed_knowledge.py`).
- [x] **Automatización de Arranque:** Bootear de manera concurrente o consecutiva a Fausto (Scheduler) y Sofy (Telegram Webhook/Polling).
- [x] **Manifiesto de Entorno:** Generar archivo `.env.example` con conectores plug-and-play.
