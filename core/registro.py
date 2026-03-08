from telegram import ReplyKeyboardMarkup, KeyboardButton
from core import db

async def manejar_paso_registro(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    
    # Aseguramos el estado en la DB antes de responder
    db.actualizar_campo_usuario(user_id, "estado_onboarding", "WHATSAPP")
    
    keyboard = [[KeyboardButton("📲 Compartir mi número de WhatsApp", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await query.message.reply_text(
        "Para brindarle una atención personalizada y segura, necesito validar su contacto.\n\n"
        "Por favor, presione el botón de abajo para compartir su número.",
        reply_markup=reply_markup
    )
