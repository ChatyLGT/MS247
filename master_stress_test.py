import asyncio
import json
import os
from unittest.mock import AsyncMock, patch, MagicMock
import datetime

# --- MOCK DB LAYER ---
class MockDB:
    def __init__(self):
        self.users = {}
        self.adn = {}
        self.equipo = {}
        self.historial = {}

    def factory_reset(self):
        self.users = {}
        self.adn = {}
        self.equipo = {}
        self.historial = {}
        print("MOCK DB: Factory Reset OK.")

    def crear_usuario(self, telegram_id, **kwargs):
        self.users[telegram_id] = {"telegram_id": telegram_id, "estado_onboarding": "NUEVO"}
        print(f"MOCK DB: Usuario {telegram_id} creado.")

    def inicializar_adn(self, telegram_id):
        self.adn[telegram_id] = {"usuario_id": telegram_id}

    def actualizar_adn(self, telegram_id, campo, valor):
        if telegram_id not in self.adn: self.adn[telegram_id] = {}
        self.adn[telegram_id][campo] = valor

    def actualizar_campo_usuario(self, telegram_id, campo, valor):
        if telegram_id not in self.users: self.users[telegram_id] = {}
        self.users[telegram_id][campo] = valor

    def obtener_usuario(self, telegram_id):
        return self.users.get(telegram_id)

    def obtener_adn_completo(self, telegram_id):
        data = self.adn.get(telegram_id, {}).copy()
        data.update(self.users.get(telegram_id, {}))
        data["equipo"] = self.equipo.get(telegram_id, [])
        return data

    def agregar_agente_equipo(self, telegram_id, **kwargs):
        if telegram_id not in self.equipo: self.equipo[telegram_id] = []
        self.equipo[telegram_id].append(kwargs)

    def guardar_memoria_hilo(self, telegram_id, rol, contenido, es_andrea=False):
        if es_andrea:
            print(f"MOCK DB: [ANDREA] {rol}: {contenido}")
        else:
            print(f"MOCK DB: [GENERIC] {rol}: {contenido}")

    def get_connection(self):
        return MagicMock()

mock_db = MockDB()

# --- PATCHING GLOBALLY ---
# We patch core.db BEFORE importing any flows that might use it.
patcher_conn = patch("core.db.get_connection", mock_db.get_connection)
patcher_act = patch("core.db.actualizar_campo_usuario", mock_db.actualizar_campo_usuario)
patcher_save = patch("core.db.guardar_memoria_hilo", mock_db.guardar_memoria_hilo)
patcher_adn = patch("core.db.obtener_adn_completo", mock_db.obtener_adn_completo)

patcher_conn.start()
patcher_act.start()
patcher_save.start()
patcher_adn.start()

# --- IMPORTS AFTER GLOBAL PATCH ---
from core import router_jero
from agentes.fase1_onboarding.josefina.flow import manejar_josefina
from agentes.fase1_onboarding.bruno.flow import manejar_bruno
from agentes.fase1_onboarding.sofy.sofy_router import manejar_onboarding
from agentes.fase4_bunker.andrea.flow import manejar_andrea

# --- CONFIGURACION DE LOGS ---
def log_step(step):
    print("\n" + "="*80)
    print(f"[STRESS TEST] {step}")
    print("="*80)

# --- SIMULATION JOURNEY ---
async def simulate_user_journey(user_id, name, rubro, level, masks=None):
    log_step(f"Viaje de {name} ({rubro}) - Nivel {level}")
    
    update = AsyncMock()
    msg_mock = AsyncMock()
    msg_mock.chat.id = user_id
    msg_mock.reply_text = AsyncMock()
    update.message = msg_mock
    update.effective_message = msg_mock
    context = AsyncMock()
    context.bot.send_message = AsyncMock()
    
    mock_db.crear_usuario(user_id, nombre_completo=name)
    mock_db.actualizar_adn(user_id, "rubro", rubro)
    mock_db.actualizar_campo_usuario(user_id, "nivel_contratado", level)
    
    # Josefina
    log_step(f"Josefina para {name}")
    res_j1 = {"mensaje": "Equipo?", "intentar_cambiar_estado": "JOSEFINA_ACTIVA", "bautismo_completado": False}
    with patch("core.gemini_multimodal.procesar_texto_puro", AsyncMock(return_value=json.dumps(res_j1))):
        await manejar_josefina(update, context, user_id, "Cultura")

    res_j2 = {"mensaje": "Bautismo OK", "intentar_cambiar_estado": "BRUNO_ACTIVO", "bautismo_completado": True}
    with patch("core.gemini_multimodal.procesar_texto_puro", AsyncMock(return_value=json.dumps(res_j2))):
        await manejar_josefina(update, context, user_id, "Me gusta")

    # Bruno
    log_step(f"Bruno para {name}")
    res_b = {"mensaje": "Plan", "intentar_cambiar_estado": "OPERACION_CONTINUA", "dias_compromiso": ["Lunes"]}
    with patch("core.gemini_multimodal.procesar_texto_puro", AsyncMock(return_value=json.dumps(res_b))):
        await manejar_bruno(update, context, user_id, "OK")

    # Sofy
    log_step(f"Sofy para {name}")
    res_s = {"mensaje": "Dossier", "intentar_cambiar_estado": "KICKOFF"}
    with patch("core.gemini_multimodal.procesar_texto_puro", AsyncMock(return_value=json.dumps(res_s))), \
         patch("core.pdf_generator.generar_pdf_dossier", MagicMock(return_value="/tmp/test.pdf")), \
         patch("builtins.open", MagicMock()):
        await manejar_onboarding(update, context, user_id, "SOFY_ACTIVA", "Gracias")

    # Kickoff
    log_step(f"Kickoff para {name}")
    if masks:
        guion = [
            {"agente": "Elon Musk", "texto": "Innovate."},
            {"agente": "Dr. House", "texto": "Everybody lies."},
            {"agente": "Quentin Tarantino", "texto": "Violence!"}
        ]
        mock_db.agregar_agente_equipo(user_id, nombre_agente="Dr. House", rol_socket="Legal", personalidad="Cinica", estilo_narrativo="Directo y Sarcástico")
    else:
        guion = [{"agente": "Jero", "texto": "Holi"}]

    with patch("core.gemini_multimodal.procesar_texto_puro", AsyncMock(return_value=json.dumps(guion))):
        await router_jero.call_kickoff({"update": update, "context": context, "telegram_id": user_id, "estado_actual": "KICKOFF"})

async def main():
    print("MASTER STRESS TEST START")
    mock_db.factory_reset()
    
    await simulate_user_journey(1001, "Don Juan", "Pan", "Consultivo")
    await simulate_user_journey(1002, "Elon Jr", "Mkt", "Maker", masks=True)
    
    # Usuario C
    log_step("Paso 1: Ricardo Crisis")
    u_id = 1003
    update = AsyncMock()
    update.message.chat.id = u_id
    update.message.text = "No puedo mas."
    update.effective_message = update.message
    
    res_route = json.dumps({"siguiente_agente": "andrea", "razonamiento": "Crisis"})
    res_andrea = "Hola, soy Andrea. Hablemos de tu crisis."
    
    with patch("core.gemini_multimodal.procesar_texto_puro", AsyncMock(side_effect=[res_route, res_andrea])):
        await router_jero.orquestar_mensaje(update, AsyncMock(), u_id, "NUEVO", "No puedo mas")
        print("Andrea Interaction OK")

    print("\nSTRESS TEST SUCCESS - ALL JOURNEYS COMPLETED")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        patcher_conn.stop()
        patcher_act.stop()
        patcher_save.stop()
        patcher_adn.stop()
