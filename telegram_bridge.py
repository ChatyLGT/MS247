import os, asyncio, tempfile
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from core import db
from core.borrado import ejecutar_borrado_total
from core.parser import parsear_evento
from agentes.fase1_onboarding.sofy.sofy_router import manejar_onboarding
from core.logger_omnisciente import obtener_chismografo, log_evento_crudo
from core.router_jero import orquestar_mensaje
from core.telemetria import consultar_gasolina

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
log = obtener_chismografo("TELEGRAM_BRIDGE")

# Memoria para silenciar reintentos de Telegram (ACK)
# YA NO USAMOS ESTO LOCALMENTE, USAMOS LA DB PARA PERSISTENCIA ENTRE REINICIOS
# PROCESSED_UPDATES = set()

async def catch_all(update, context):
    if not update.update_id: return
    
    # 1. Verificación de Duplicidad en DB (Regla de Oro para evitar el Loop del VPS)
    if db.es_peticion_duplicada(update.update_id):
        log.warning(f"🚫 [DUPLICADO] Ignorando update_id {update.update_id}")
        return
    
    db.registrar_peticion_procesada(update.update_id)

    user = update.effective_user
    if not user: return
    message = update.message
    if not message: return
    
    # Filtro de Contenido Basura
    if message.sticker or message.animation or message.video:
        await message.reply_text("🙏 <i>Sofy: Por ahora solo proceso texto, audios cortos o documentos PDF/Imágenes clave.</i>", parse_mode="HTML")
        return

    identidad, tipo, contenido, user_data = parsear_evento(update)
    log_evento_crudo("TELEGRAM_BRIDGE", f"📥 EVENTO ENTRANTE [{tipo}] de {user.id}", update.to_dict())
    
    db_user = db.obtener_usuario(user.id)
    if not db_user:
        db.crear_usuario(user.id, None, None, user.language_code)
        db.inicializar_adn(user.id)
        estado = "NUEVO"
    else:
        estado = db_user.get('estado_onboarding')

    # Captura de contacto (Paso 7 y 8)
    if tipo == "CONTACTO":
        phone = update.message.contact.phone_number
        db.actualizar_campo_usuario(user.id, "telefono_whatsapp", phone)
        db.actualizar_campo_usuario(user.id, "estado_onboarding", "TYC")
        estado = "TYC"
        
    custom_path = None
    try:
        # Detectar Audio/Voice
        if message.voice or message.audio or message.document or message.photo:
            attachment = message.voice or message.audio or message.document
            if message.photo: attachment = message.photo[-1] # Best quality
            
            file_id = attachment.file_id
            file = await context.bot.get_file(file_id)
            
            # Simple extension guess
            ext = ".ogg" if message.voice else ".file"
            if message.document:
                ext = os.path.splitext(attachment.file_name)[1] if hasattr(attachment, 'file_name') and attachment.file_name else ".file"
            elif message.photo: ext = ".jpg"
                
            custom_path = os.path.join(tempfile.gettempdir(), f"ms247_{file_id}{ext}")
            await file.download_to_drive(custom_path)

        await orquestar_mensaje(update, context, user.id, estado, contenido, file_path=custom_path)
    except Exception as e:
        log.error(f"⚠️ [TELEGRAM_BRIDGE] Falla no manejada para user {user.id}: {e}")
        try:
            # Mensaje empático pero que no incita a reintento inmediato desesperado
            await message.reply_text("⏳ <i>Sofy: Tu petición está tomando más de lo normal, pero ya la tengo en cola. No hace falta que la reenvíes, te respondo en cuanto procese los datos...</i>", parse_mode="HTML")
        except: pass 
    finally:
        # Seguridad Nivel 0: Limpieza obligatoria sin importar Exceptions
        if custom_path and os.path.exists(custom_path):
            try:
                os.remove(custom_path)
                log.info(f"🧹 [CLEANUP] Archivo temporal {custom_path} eliminado.")
            except Exception as cleanup_error:
                log.error(f"🚨 [CLEANUP FAILED] No se pudo borrar {custom_path}: {cleanup_error}")

async def manejar_callback(update, context):
    query = update.callback_query
    user = update.effective_user
    await query.answer()
    
    db_user = db.obtener_usuario(user.id)
    estado = db_user.get('estado_onboarding') if db_user else "NUEVO"
    log.info(f"🔘 [BOTÓN] {query.data} de {user.id}")

    if query.data == "start_flow":
        db.actualizar_campo_usuario(user.id, "estado_onboarding", "WHATSAPP")
        await orquestar_mensaje(update, context, user.id, "WHATSAPP", "Iniciar Registro")
    elif query.data == "acepto_tyc":
        db.actualizar_campo_usuario(user.id, "estado_onboarding", "DATOS")
        await orquestar_mensaje(update, context, user.id, "DATOS", "Acepto")
    elif query.data == "confirmacion_ok":
        db.actualizar_campo_usuario(user.id, "estado_onboarding", "PASO_PEPE")
        await orquestar_mensaje(update, context, user.id, "PASO_PEPE", "Confirmación Exitosa")
    elif query.data == "ir_a_pepe":
        db.actualizar_campo_usuario(user.id, "estado_onboarding", "PEPE_ACTIVO")
        await orquestar_mensaje(update, context, user.id, "PEPE_ACTIVO", "INICIAR_DIAGNOSTICO")
    elif query.data == "pepe_avanzar_maria":
        db.actualizar_campo_usuario(user.id, "estado_onboarding", "MARIA_ACTIVO")
        await orquestar_mensaje(update, context, user.id, "MARIA_ACTIVO", "INICIAR_ARQUITECTURA")
    elif query.data == "pepe_mas_contexto":
        await orquestar_mensaje(update, context, user.id, "PEPE_ACTIVO", "Quiero seguir profundizando los detalles de mi modelo de negocio.")

if __name__ == '__main__':
    log.info("🚀 Matriz activa. UX de Pepe y Handoff conectados.")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("eraseall", ejecutar_borrado_total))
    app.add_handler(CommandHandler("gasolina", consultar_gasolina))
    app.add_handler(CallbackQueryHandler(manejar_callback))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, catch_all))
    app.run_polling()
