
import os
import asyncio
from datetime import datetime, time
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
import yfinance as yf

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ZONA_HORARIA = ZoneInfo("Europe/Madrid")


def obtener_estado_fondo():
    try:
        ticker_symbol = "0P00011HBM.F"
        fondo = yf.Ticker(ticker_symbol)

        historial = fondo.history(period="10d")

        if len(historial) < 2:
            return (
                "⚠️ No se han encontrado datos suficientes "
                "para este fondo en Yahoo Finance."
            )

        info_fondo = fondo.info
        nombre_fondo = (
            info_fondo.get("longName")
            or info_fondo.get("shortName")
        )
        moneda = info_fondo.get("currency", "EUR")

        precio_actual = historial["Close"].iloc[-1]
        fecha_actual_dt = historial.index[-1]
        precio_anterior = historial["Close"].iloc[-2]
        fecha_anterior_dt = historial.index[-2]

        fecha_actual_str = fecha_actual_dt.strftime("%d/%m/%Y")
        fecha_anterior_str = fecha_anterior_dt.strftime("%d/%m/%Y")

        hoy = datetime.now(ZONA_HORARIA).date()

        if fecha_actual_dt.date() == hoy:
            estado_actualizacion = (
                "✅ **El precio está actualizado al día de hoy.**"
            )
        else:
            estado_actualizacion = (
                "⏳ **Precio pendiente de actualización** "
                f"(Último dato disponible: {fecha_actual_str})."
            )

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

        mensaje = (
            "💼 **ESTADO DEL FONDO INDEXADO**\n\n"
            f"🏦 **Fondo:** {nombre_fondo} (`0P00011HBM`)\n"
            f"📅 **Fecha del precio:** {fecha_actual_str}\n"
            f"💰 **NAV Actual:** *{precio_actual:.2f} {moneda}*\n"
            f"⏮️ **Día anterior registrado:** {fecha_anterior_str}\n"
            f"{icono} **Variación:** {tendencia} "
            f"({signo}{diferencia:.2f} {moneda} | "
            f"{signo}{porcentaje:.2f}%)\n\n"
            f"ℹ️ {estado_actualizacion}"
        )

        return mensaje

    except Exception as e:
        return (
            "❌ Error al obtener la información financiera: "
            f"`{str(e)}`"
        )


async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "🔍 Consultando el fondo indexado..."
    )

    mensaje = await asyncio.to_thread(obtener_estado_fondo)

    await update.message.reply_text(
        mensaje,
        parse_mode="Markdown",
    )


async def envio_programado(
    context: ContextTypes.DEFAULT_TYPE,
):
    mensaje = await asyncio.to_thread(obtener_estado_fondo)

    await context.bot.send_message(
        chat_id=int(CHAT_ID),
        text=mensaje,
        parse_mode="Markdown",
    )


async def main():
    if not BOT_TOKEN:
        raise ValueError("Falta BOT_TOKEN en el archivo .env")

    if not CHAT_ID:
        raise ValueError(
            "Falta TELEGRAM_CHAT_ID en el archivo .env"
        )

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Mantener el comando manual como alternativa
    app.add_handler(CommandHandler("status", status))
    
    # Enviar el informe automáticamente cada día a las 23:00
    if app.job_queue is None:
        raise RuntimeError(
            'Instala la dependencia con: '
            'pip install "python-telegram-bot[job-queue]"'
        )

    app.job_queue.run_daily(
        envio_programado,
        time=time(23, 0, tzinfo=ZONA_HORARIA),
        name="informe_diario_fondo",
    )

    print(
        "Bot iniciado. Informe diario programado "
        "a las 23:00, hora de España peninsular."
    )

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    try:
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
