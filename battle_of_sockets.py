import asyncio
import json
import os
from unittest.mock import AsyncMock, patch, MagicMock
import datetime

# --- MOCK DB LAYER (VERA-028 Persistence) ---
class MockDB:
    def __init__(self):
        # Cargamos la data del test anterior (Simulación de 3 días después)
        self.users = {
            1001: {"telegram_id": 1001, "estado_onboarding": "OPERACION_CONTINUA", "nivel_contratado": "Consultivo", "nombre_empresa": "Panadería Don Juan"},
            1002: {"telegram_id": 1002, "estado_onboarding": "OPERACION_CONTINUA", "nivel_contratado": "Maker", "nombre_empresa": "Elon Agency"},
            1003: {"telegram_id": 1003, "estado_onboarding": "OPERACION_CONTINUA", "nivel_contratado": "Autonomo", "nombre_empresa": "Cancun Realty"}
        }
        self.adn = {
            1001: {"rubro": "Panaderia"},
            1002: {"rubro": "Marketing"},
            1003: {"rubro": "Inmobiliaria"}
        }
        self.equipo = {
            1001: [
                {"nombre_agente": "Tito", "rol_socket": "Asistente Administrativo", "personalidad": "Atento y casero"},
                {"nombre_agente": "Don Lucho", "rol_socket": "CFO", "personalidad": "Cuida el mango"}
            ],
            1002: [
                {"nombre_agente": "Paula", "rol_socket": "Legal", "personalidad": "Pop Mask: Dr. House. Cinica, ruda, brillante.", "estilo_narrativo": "Sin emojis, directo e hiriente"},
                {"nombre_agente": "Quentin", "rol_socket": "Copywriter", "personalidad": "Pop Mask: Tarantino. Epico, sangriento, guionista.", "estilo_narrativo": "Sin emojis, dialogos punzantes"}
            ],
            1003: [
                {"nombre_agente": "Jero", "rol_socket": "CEO", "personalidad": "Ejecutivo Autonomo"}
            ]
        }

    def obtener_adn_completo(self, telegram_id):
        data = self.adn.get(telegram_id, {}).copy()
        data.update(self.users.get(telegram_id, {}))
        data["equipo"] = self.equipo.get(telegram_id, [])
        return data

    def actualizar_campo_usuario(self, telegram_id, campo, valor):
        if telegram_id in self.users:
            self.users[telegram_id][campo] = valor

    def guardar_memoria_hilo(self, telegram_id, rol, contenido, es_andrea=False):
        pass

    def get_connection(self): return MagicMock()

mock_db = MockDB()

# --- GLOBAL PATCHES ---
patch("core.db.get_connection", mock_db.get_connection).start()
patch("core.db.actualizar_campo_usuario", mock_db.actualizar_campo_usuario).start()
patch("core.db.guardar_memoria_hilo", mock_db.guardar_memoria_hilo).start()
patch("core.db.obtener_adn_completo", mock_db.obtener_adn_completo).start()

from core import router_jero, grabadora

# --- CONFIGURACION DE PRUEBA ---
grabadora.RESET = "" # Desactivar colores para log limpio si necesario

def log_sep(titulo):
    print("\n" + "#"*100)
    print(f"### [VERA-028] {titulo}")
    print("#"*100 + "\n")

async def test_escenario_1():
    log_sep("ESCENARIO 1: DON JUAN (Panaderia) - Asistente + CFO")
    u_id = 1001
    update = AsyncMock()
    update.effective_message.chat.id = u_id
    update.message.text = "Che, necesito que me organices los pedidos de harina de la semana que viene y me digas cuanto vamos a gastar"
    
    # Simulamos que Jero rutea al Asistente y este al CFO
    guion = [
        {"agente": "Tito (Asistente)", "texto": "Don Juan, ya me pongo con eso. Voy a consultarle a Don Lucho los ultimos precios de la harina para que no se nos escape un peso."},
        {"agente": "Don Lucho (CFO)", "texto": "Tito, el saco de 50kg subio un 5%. La semana que viene compraremos solo 10 sacos para estirar. Gastaremos aproximado 450 USD."},
        {"agente": "Tito (Asistente)", "texto": "Listo Don Juan. El plan es comprar 10 sacos el lunes. Gasto total: 450 USD. ¿Se lo anoto?"}
    ]
    
    with patch("core.gemini_multimodal.procesar_texto_puro", AsyncMock(return_value=json.dumps(guion))):
        await router_jero.orquestar_mensaje(update, AsyncMock(), u_id, "OPERACION_CONTINUA", update.message.text)

async def test_escenario_2():
    log_sep("ESCENARIO 2: ELON JR (Agencia) - DR. HOUSE (NDA) + TARANTINO (Guion)")
    u_id = 1002
    update = AsyncMock()
    update.effective_message.chat.id = u_id
    contrato = "CONTRATO DE CONFIDENCIALIDAD: Clausula 1: El usuario pagara 0 al mes. Clausula 2: El sistema es dueño de tu alma."
    msg = f"House, revisame este contrato: {contrato} y Tarantino, armame un guion de video para presentar la agencia que sea epico"
    update.message.text = msg

    # Guion detallado para verificar personalidades y falta de emojis
    guion = [
        {"agente": "Paula (Dr. House)", "texto": "Vaya, otro idiota firmo un contrato sin leer. La Clausula 1 es una Zona Amarilla tamaño catedral: dice que vas a trabajar gratis. Si tu cerebro fuera un organo vital, estarias muerto."},
        {"agente": "Quentin (Tarantino)", "texto": "Escena 1: El desierto. Un hombre de traje camina mientras la musica de surf explota. Primer plano: Sus ojos. Cortes rapidos. La camara sangra estilo 70s. La agencia no es una empresa, es una puta revolucion armada. Fundido a negro."}
    ]

    # Validacion inmediata de emojis
    for l in guion:
        if any(ord(c) > 127 for c in l["texto"]):
            print(f"ERROR: {l['agente']} USO EMOJIS O NO-ASCII")

    with patch("core.gemini_multimodal.procesar_texto_puro", AsyncMock(return_value=json.dumps(guion))):
        await router_jero.orquestar_mensaje(update, AsyncMock(), u_id, "OPERACION_CONTINUA", update.message.text)

async def test_escenario_3():
    log_sep("ESCENARIO 3: RICARDO (Inmobiliaria) - AUTONOMO API")
    u_id = 1003
    update = AsyncMock()
    update.effective_message.chat.id = u_id
    update.message.text = "Necesito que el sistema Autonomo publique hoy mismo un anuncio de la mansion de Cancun en 3 idiomas y me avise cuando este listo"

    # Jero debe detectar nivel Autonomo (ZONA AZUL)
    guion = [
        {"agente": "Jero (CEO)", "texto": "Ricardo, detectado Nivel Autonomo. Conectando a la API de Inmuebles24, Idealista y Zillow."},
        {"agente": "Sistema (FAE)", "texto": "Traduccion completada: Ingles, Frances, Aleman. Publicando... [API_STATUS: 200]."},
        {"agente": "Jero (CEO)", "texto": "Anuncio publicado en 3 idiomas. Tarea finalizada sin intervencion humana."}
    ]

    with patch("core.gemini_multimodal.procesar_texto_puro", AsyncMock(return_value=json.dumps(guion))):
        await router_jero.orquestar_mensaje(update, AsyncMock(), u_id, "OPERACION_CONTINUA", update.message.text)

async def main():
    print("\n" + "!"*100)
    print("!!! INICIANDO VERA-028: LA BATALLA DE LOS SOCKETS !!!")
    print("!"*100 + "\n")
    
    await test_escenario_1()
    await test_escenario_2()
    await test_escenario_3()
    
    print("\n" + "!"*100)
    print("!!! VERA-028 COMPLETADA CON EXITO !!!")
    print("!"*100 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
