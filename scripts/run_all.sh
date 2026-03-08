#!/bin/bash

echo "🚀 [SISTEMA DE TITANIO] - Reiniciando motores..."

# Matar procesos de forma agresiva
pkill -9 -f "telegram_bridge.py"
pkill -9 -f "core/motor_fausto.py"
sleep 2 # Esperamos a que la API de Telegram se de cuenta que nos desconectamos

# Arrancar con -u (Unbuffered) para logs en tiempo real
python3 -u telegram_bridge.py > logs_bridge.txt 2>&1 &
python3 -u core/motor_fausto.py > logs_fausto.txt 2>&1 &

echo "✅ Motores encendidos."
echo "🔎 Para ver el chisme en tiempo real: tail -f logs_bridge.txt"
