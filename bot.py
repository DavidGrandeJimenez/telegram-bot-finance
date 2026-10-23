import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import yfinance as yf

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Consultando el fondo indexado...")
    
    try:
        ticker_symbol = "0P00011HBM.F"
        fondo = yf.Ticker(ticker_symbol)
        
        # Historial de los últimos 10 días para asegurar registros
        historial = fondo.history(period="10d")
        
        if len(historial) >= 2:
            # 1. Extraer el nombre del fondo (con fallback si la API no lo trae)
            info_fondo = fondo.info
            nombre_fondo = info_fondo.get('longName') or info_fondo.get('shortName') or "Vanguard Global Stock Index Fund"
            moneda = info_fondo.get('currency', 'EUR')
            
            # 2. Extraer precios y fechas
            precio_actual = historial['Close'].iloc[-1]
            fecha_actual_dt = historial.index[-1]
            
            precio_anterior = historial['Close'].iloc[-2]
            fecha_anterior_dt = historial.index[-2]
            
            # Formatear fechas a DD/MM/YYYY
            fecha_actual_str = fecha_actual_dt.strftime('%d/%m/%Y')
            fecha_anterior_str = fecha_anterior_dt.strftime('%d/%m/%Y')
            
            # 3. Comprobar si está actualizado al día de hoy
            hoy_str = datetime.now().strftime('%d/%m/%Y')
            if fecha_actual_str == hoy_str:
                estado_actualizacion = "✅ **El precio está actualizado al día de hoy.**"
            else:
                estado_actualizacion = f"⏳ **Precio pendiente de actualización** (Último dato disponible: {fecha_actual_str})."
            
            # 4. Cálculo de diferencias y porcentajes
            diferencia = precio_actual - precio_anterior
            porcentaje = (diferencia / precio_anterior) * 100
            
            if diferencia >= 0:
                icono = "🟢"
                tendencia = "📈 Sube"
                signo = "+"
            else:
                icono = "🔴"
                tendencia = "📉 Baja"
                signo = ""
            
            # 5. Construcción del mensaje para Telegram
            mensaje = (
                f"💼 **ESTADO DEL FONDO INDEXADO**\n\n"
                f"🏦 **Fondo:** {nombre_fondo} (`0P00011HBM`)\n"
                f"📅 **Fecha del precio:** {fecha_actual_str}\n"
                f"💰 **NAV Actual:** *{precio_actual:.2f} {moneda}*\n"
                f"⏮️ **Día anterior registrado:** {fecha_anterior_str}\n"
                f"{icono} **Variación:** {tendencia} ({signo}{diferencia:.2f} {moneda} | {signo}{porcentaje:.2f}%)\n\n"
                f"ℹ️ {estado_actualizacion}"
            )
        else:
            mensaje = "⚠️ No se han encontrado datos suficientes para este fondo en Yahoo Finance."
            
    except Exception as e:
        mensaje = f"❌ Ocurrió un error al obtener la información financiera: `{str(e)}`"

    await update.message.reply_text(mensaje, parse_mode="Markdown")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("status", status))

    print("Bot iniciado con formato personalizado. Esperando el comando /status...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass

    await app.updater.stop()
    await app.stop()
    await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())