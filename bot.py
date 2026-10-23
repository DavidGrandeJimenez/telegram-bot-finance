import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import yfinance as yf

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Consultando el fondo indexado...")
    
    try:
        # Ticker de Yahoo Finance para el fondo (Morningstar ID + sufijo .F)
        ticker_symbol = "0P00011HBM.F"
        fondo = yf.Ticker(ticker_symbol)
        
        # Pedimos un historial de 10 días para garantizar que obtenemos al menos 2 días con cotización válida
        historial = fondo.history(period="10d")
        
        if len(historial) >= 2:
            # Extraer datos del último día con registro
            precio_actual = historial['Close'].iloc[-1]
            fecha_actual = historial.index[-1].strftime('%Y-%m-%d')
            
            # Extraer datos del día anterior con registro disponible
            precio_anterior = historial['Close'].iloc[-2]
            fecha_anterior = historial.index[-2].strftime('%Y-%m-%d')
            
            # Calcular diferencias
            diferencia = precio_actual - precio_anterior
            porcentaje = (diferencia / precio_anterior) * 100
            
            moneda = fondo.info.get('currency', 'EUR')
            
            # Lógica para asignar emojis y colores visuales según la tendencia
            if diferencia >= 0:
                icono = "🟢"
                tendencia = "📈 Sube"
                signo = "+"
            else:
                icono = "🔴"
                tendencia = "📉 Baja"
                signo = "" # El número negativo ya incluye su propio signo "-"
            
            mensaje = (
                f"💼 **ESTADO DEL FONDO INDEXADO**\n\n"
                f"🆔 **ID Morningstar:** `0P00011HBM`\n"
                f"📅 **Fecha:** {fecha_actual}\n"
                f"💰 **NAV Actual:** *{precio_actual:.2f} {moneda}*\n"
                f"⏮️ **Día anterior:** {fecha_anterior}\n"
                f"{icono} **Variación:** {tendencia} ({signo}{diferencia:.2f} {moneda} | {signo}{porcentaje:.2f}%)"
            )
        elif len(historial) == 1:
            precio_actual = historial['Close'].iloc[-1]
            fecha_actual = historial.index[-1].strftime('%Y-%m-%d')
            moneda = fondo.info.get('currency', 'EUR')
            mensaje = (
                f"💼 **ESTADO DEL FONDO INDEXADO**\n\n"
                f"🆔 **ID Morningstar:** `0P00011HBM`\n"
                f"📅 **Fecha:** {fecha_actual}\n"
                f"💰 **NAV Actual:** *{precio_actual:.2f} {moneda}*\n"
                f"⚠️ Hay un único registro disponible, no se puede calcular la diferencia."
            )
        else:
            mensaje = "⚠️ No se han encontrado datos recientes para este fondo en Yahoo Finance."
            
    except Exception as e:
        mensaje = f"❌ Ocurrió un error al obtener la información financiera: `{str(e)}`"

    await update.message.reply_text(mensaje, parse_mode="Markdown")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Registramos el comando /status basado en la estructura inicial del bot[cite: 1]
    app.add_handler(CommandHandler("status", status))

    print("Bot iniciado con diseño visual avanzado. Esperando el comando /status...")

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