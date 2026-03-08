from core import db
from core import auditor
from telegram import ReplyKeyboardRemove
from core.grabadora import log_terminal

async def ejecutar_borrado_total(update, context):
    user = update.effective_user
    if not context.args or context.args[0] != "Chaty2026":
        await update.message.reply_text("⛔ Clave incorrecta. Bóveda intacta.")
        return

    # 1. Borrado físico en la DB
    db.borrar_usuario(user.id)
    
    # 2. Log anónimo (Regla #7: Sin usar metadatos de Telegram)
    log_terminal("SISTEMA", "NUEVO USUARIO", "💥 BÓVEDA PURGADA - Borrado absoluto")
    
    await update.message.reply_text(
        "💥 **Bóveda Purificada.**\n\nBorré tu registro y tu ADN. Ahora sos un desconocido. Tirá /start para volver.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
