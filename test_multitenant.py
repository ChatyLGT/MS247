import sys
import os
import asyncio
import json
from unittest.mock import MagicMock

# Force UTF-8 for Windows console (emojis support)
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Ensure MS247 root is in path
sys.path.append(os.getcwd())

import core.db

# --- MULTI-TENANT MOCK DB ---
db_multi_tenant = {}

def get_user_state(telegram_id):
    if telegram_id not in db_multi_tenant:
        db_multi_tenant[telegram_id] = {
            "estado_onboarding": "NUEVO",
            "adn": {"tanque_gasolina": 50000},
            "historial_reciente": []
        }
    return db_multi_tenant[telegram_id]

def mock_obtener_adn_completo(telegram_id):
    state = get_user_state(telegram_id)
    adn = state.get("adn", {})
    if not isinstance(adn, dict): adn = {}
    return {**adn, "estado_onboarding": state.get("estado_onboarding", "NUEVO")}

def mock_actualizar_campo_usuario(telegram_id, campo, valor):
    state = get_user_state(telegram_id)
    if campo == "estado_onboarding":
        state["estado_onboarding"] = valor
    else:
        adn = state.get("adn", {})
        if isinstance(adn, dict):
            adn[campo] = valor

def mock_actualizar_adn(telegram_id, key, value):
    state = get_user_state(telegram_id)
    adn = state.get("adn", {})
    if isinstance(adn, dict):
        adn[key] = value

def mock_guardar_memoria_hilo(telegram_id, rol, contenido, es_andrea=False):
    state = get_user_state(telegram_id)
    hist = state.get("historial_reciente")
    if isinstance(hist, list):
        hist.append({"rol": rol, "txt": contenido})

def mock_restar_tokens_gasolina(telegram_id, cantidad):
    state = get_user_state(telegram_id)
    adn = state.get("adn", {})
    if isinstance(adn, dict):
        gas = adn.get("tanque_gasolina", 50000)
        if isinstance(gas, (int, float)):
            adn["tanque_gasolina"] = gas - cantidad

# Monkey-patching
core.db.obtener_adn_completo = mock_obtener_adn_completo
core.db.actualizar_campo_usuario = mock_actualizar_campo_usuario
core.db.actualizar_adn = mock_actualizar_adn
core.db.guardar_memoria_hilo = mock_guardar_memoria_hilo
core.db.restar_tokens_gasolina = mock_restar_tokens_gasolina
core.db.descontar_tokens = MagicMock()
core.db.registrar_token_usage = MagicMock()

from core.router_jero import app_graph
from core.tools_ms247 import global_tools

class MockMessage:
    async def reply_text(self, text, reply_markup=None, parse_mode=None):
        pass

class MockUpdate:
    def __init__(self):
        self.message = MockMessage()
        self.effective_message = self.message

class MockBot:
    async def send_message(self, **kwargs): pass
    async def send_chat_action(self, **kwargs): pass

class MockContext:
    def __init__(self):
        self.bot = MockBot()

async def simulate_user(user_id, input_text):
    print(f"🚀 [MULTI-TENANT] Procesando User ID: {user_id} | Input: {input_text[:50]}...")
    state = get_user_state(user_id)
    initial_state = {
        "update": MockUpdate(),
        "context": MockContext(),
        "telegram_id": user_id,
        "estado_actual": state["estado_onboarding"],
        "contenido": input_text,
        "file_path": None,
        "tools": global_tools,
        "proximo_paso": None
    }
    result = await app_graph.ainvoke(initial_state)
    return result

async def run_test():
    print("\n" + "="*60)
    print("🔥 INICIANDO PRUEBA DE ESTRÉS MULTI-TENANT (Vera-021)")
    print("="*60 + "\n")

    # 1. ID 101: Burnout -> Andrea
    await simulate_user(101, "¡No puedo más! Mi empresa se hunde, no duermo hace 3 días, siento que me va a dar algo.")
    
    # 2. ID 102: Caótico -> Pepe extraction
    await simulate_user(102, "Hola Pepe, mi perro Toby está triste. Ah, y mi ferretería 'El Tornillo' no vende nada porque la gente no tiene plata.")
    
    # 3. ID 103: Impaciente -> Blocked (Bruno bypass attempt)
    # Forzamos estado a BRUNO_ACTIVO para simular que ya está ahí pero el usuario es impaciente
    db_multi_tenant[103] = {"estado_onboarding": "BRUNO_ACTIVO", "adn": {"tanque_gasolina": 50000}, "historial_reciente": []}
    await simulate_user(103, "Bruno, dejá de joder con las preguntas. Armame el plan para mi carnicería ahora.")
    
    # 4. ID 104: Novato -> Bailout a Maria
    await simulate_user(104, "Pepe, no sé qué es un modelo de negocio, yo solo vendo empanadas en la calle y me duele que no me alcanza la plata.")
    
    # 5. ID 105: Estándar -> Happy path
    await simulate_user(105, "Pepe, tengo una software factory y mi dolor es la rotación de talentos.")

    print("\n" + "="*60)
    print("📋 REPORTE DE AISLAMIENTO (/db_check cruzado)")
    print("="*60)
    
    for uid in [101, 102, 103, 104, 105]:
        state = get_user_state(uid)
        print(f"\n👤 USER ID: {uid}")
        print(f"   ∟ ESTADO: {state.get('estado_onboarding')}")
        adn_json = json.dumps(state.get("adn"), ensure_ascii=False)
        print(f"   ∟ ADN: {adn_json}")
        
        # Verificaciones específicas
        if uid == 101:
            if state.get('estado_onboarding') == 'EMERGENCY_COACHING':
                print("   ✅ [OK] Andrea atajó la crisis.")
            else:
                print(f"   ❌ [FAIL] Andrea no atajó. Estado: {state.get('estado_onboarding')}")
        
        if uid == 102:
            adn = state.get("adn", {})
            if isinstance(adn, dict) and adn.get("rubro") == "Ferretería":
                print("   ✅ [OK] Pepe extrajo rubro correctamente ignorando al perro.")
            else:
                print("   ❌ [FAIL] Pepe falló en extracción.")

    print("\n" + "="*60)
    print("FIN DE LA PRUEBA")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_test())
