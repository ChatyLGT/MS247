"""
Módulo Simulado para Pagos de Stripe y Upselling Dinámico.
En un entorno de producción, esto usaría la librería oficial 'stripe'.
"""

import logging
from core.logger_omnisciente import obtener_chismografo

log = obtener_chismografo("STRIPE_PAGOS")

class StripeDeclinedError(Exception):
    pass

def crear_o_recuperar_customer(telegram_id: int, email: str, nombre: str):
    """
    Simula la recuperación o creación de un cliente en Stripe.
    Devuelve IDs ficticios que se guardarían en la tabla de usuarios.
    """
    log.info(f"STRIPE MOCK: Buscando/Creando Customer para {telegram_id} ({email})")
    
    # Simulación
    fake_customer_id = f"cus_mock_{telegram_id}"
    fake_pm_id = f"pm_card_mock_{telegram_id}"
    
    return fake_customer_id, fake_pm_id

async def ejecutar_cobro_upgrade(telegram_id: int, monto_usd: int, descripcion: str, force_fail=False):
    """
    Simula el cobro dinámico al usuario usando la tarjeta "On File".
    Lanza StripeDeclinedError si hay problemas (simulable con force_fail=True).
    Devuelve los últimos 4 dígitos de la tarjeta cargada y un link al recibo.
    """
    log.info(f"STRIPE MOCK: Intentando cobro automático a {telegram_id} por ${monto_usd} USD ({descripcion})")
    
    import asyncio
    await asyncio.sleep(1) # Simular latencia de red de pasarela de pago
    
    if force_fail:
        log.error(f"STRIPE MOCK: ❌ Pago rechazado (Fondos insuficientes o fallo de banco) para {telegram_id}")
        raise StripeDeclinedError("Fallo en la tarjeta. Pago declinado.")
        
    log.info(f"STRIPE MOCK: ✅ Cobro de ${monto_usd} procesado con éxito para {telegram_id}")
    
    return {
        "status": "succeeded",
        "amount": monto_usd,
        "last4": "4242",
        "receipt_url": "https://stripe.com/receipts/mock_12345"
    }
