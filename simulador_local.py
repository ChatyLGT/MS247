import sys
import os
import asyncio
import json

# Force UTF-8 for Windows console (emojis support)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure MS247 root is in path
sys.path.append(os.getcwd())

from unittest.mock import MagicMock
import core.db

# In-memory Mock DB for Local Testing
db_mock_state = {
    "estado_onboarding": "NUEVO",
    "adn": {},
    "historial_reciente": []
}

def mock_obtener_adn_completo(telegram_id):
    return db_mock_state["adn"]

def mock_actualizar_campo_usuario(telegram_id, campo, valor):
    if campo == "estado_onboarding":
        db_mock_state["estado_onboarding"] = valor
    else:
        db_mock_state["adn"][campo] = valor

def mock_actualizar_adn(telegram_id, key, value):
    db_mock_state["adn"][key] = value

def mock_guardar_memoria_hilo(telegram_id, rol, contenido, es_andrea=False):
    db_mock_state["historial_reciente"].append({"rol": rol, "txt": contenido})

def mock_restar_tokens_gasolina(telegram_id, cantidad):
    pass

core.db.obtener_adn_completo = mock_obtener_adn_completo
core.db.actualizar_campo_usuario = mock_actualizar_campo_usuario
core.db.actualizar_adn = mock_actualizar_adn
core.db.guardar_memoria_hilo = mock_guardar_memoria_hilo
core.db.descontar_tokens = MagicMock()
core.db.registrar_token_usage = MagicMock()
core.db.restar_tokens_gasolina = mock_restar_tokens_gasolina

from core.router_jero import app_graph
from core.tools_ms247 import global_tools

class MockMessage:
    async def reply_text(self, text, reply_markup=None, parse_mode=None):
        print(f"\n[BOT RESPUESTA a través de Message]:\n{text}")

    async def delete(self):
        pass

class MockUpdate:
    def __init__(self):
        self.message = MockMessage()
        self.effective_message = self.message

class MockBot:
    async def send_message(self, chat_id, text, reply_markup=None, parse_mode=None):
        print(f"\n[BOT RESPUESTA a través de Bot.send_message]:\n{text}")
    
    async def send_chat_action(self, chat_id, action):
        pass

class MockContext:
    def __init__(self):
        self.bot = MockBot()

async def main():
    print("=======================================================")
    print("SIMULADOR LOCAL - MS247 (Modo Consola)")
    print("Escribe comandos CLI empezando con '/' o chat normal.")
    print("Comandos disponibles: /estado <ESTADO>, /reset, /db_check")
    print("Escribe 'salir' para terminar.")
    print("=======================================================\n")
    
    mock_update = MockUpdate()
    mock_context = MockContext()
    test_id = 99999
    
    while True:
        try:
            texto_usuario = input(f"\n[Estado: {db_mock_state['estado_onboarding']}] Tu: ")
            
            if texto_usuario.lower() in ['salir', 'exit', 'quit']:
                break
            if not texto_usuario.strip():
                continue
                
            # Interceptores CLI
            if texto_usuario.startswith("/estado "):
                _, nuevo_estado = texto_usuario.split(" ", 1)
                db_mock_state["estado_onboarding"] = nuevo_estado.strip()
                print(f"✅ ESTADO FORZADO A: {db_mock_state['estado_onboarding']}")
                continue
                
            if texto_usuario.strip() in ["/reset", "/eraseall Chaty2026"]:
                db_mock_state["estado_onboarding"] = "NUEVO"
                db_mock_state["adn"] = {}
                db_mock_state["historial_reciente"] = []
                print("🔄 MEMORIA LOCAL BORRADA. Empezando de cero.")
                continue
                
            if texto_usuario.strip() == "/db_check":
                print("\n📊 [POSTGRESQL MOCK] ADN DEL USUARIO:")
                print(json.dumps(db_mock_state["adn"], indent=2, ensure_ascii=False))
                print(f"ESTADO ONBOARDING: {db_mock_state['estado_onboarding']}")
                continue
            
            print("Orquestando mensaje...\n")
            
            initial_state = {
                "update": mock_update,
                "context": mock_context,
                "telegram_id": test_id,
                "estado_actual": db_mock_state["estado_onboarding"],
                "contenido": texto_usuario,
                "file_path": None,
                "tools": global_tools,
                "proximo_paso": None
            }
            
            # Ejecutar el grafo de LangGraph localmente
            result = await app_graph.ainvoke(initial_state)
            
            # Eliminada la sobrescritura del estado ya que la DB es la única fuente de verdad
            
            print(f"\n[DEERFLOW RUTEO]: El Supervisor Jero decidió enviar la tarea al nodo -> '{result.get('proximo_paso', 'No definido')}'")
            
        except EOFError:
            break
        except Exception as e:
            print(f"\nError en simulador: {e}")
            import traceback
            traceback.print_exc()
            break

if __name__ == "__main__":
    asyncio.run(main())
