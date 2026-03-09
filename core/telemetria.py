from core import db

async def consultar_gasolina(update, context):
    user = update.effective_user
    u = db.obtener_usuario(user.id)
    
    if not u:
        await update.message.reply_text("❌ No se encontró tu perfil en la base de datos.")
        return
        
    tanque = u.get("tanque_gasolina", 0)
    
    # Cálculo aproximado de costo (Flash 2.0 es barato, aprox $0.10 por millón de tokens)
    costo_estimado = (tanque / 1_000_000) * 0.10 
    
    msg = f"""
⛽ <b>TELEMETRÍA: TANQUE DE GASOLINA</b>

🔹 <b>Tokens Consumidos (Sesión):</b> {tanque:,}
🔹 <b>Costo Estimado (USD):</b> ${costo_estimado:.4f}

<i>Nota: La gasolina se recarga según tu plan de consultoría. Si llegas a cero, la Mesa Directiva entrará en modo hibernación.</i>
"""
    await update.message.reply_text(msg, parse_mode="HTML")
