from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application
import db_helper
from datetime import datetime

CHANNEL_ID = -1003000835578  # Statistik Pengguna Bot

async def send_daily_report(application: Application):
    """Sends the daily user count report."""
    user_count = db_helper.count_users()
    report_message = (
        f"Laporan Harian - {datetime.now().strftime('%d %B %Y')}\n"
        f"Jumlah pengguna terdaftar: {user_count}"
    )
    await application.bot.send_message(chat_id=CHANNEL_ID, text=report_message)

def start_scheduler(application: Application):
    """Starts the scheduler for daily reports."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_report, 'interval', hours=24, args=[application])
    scheduler.start()
    print("Reporting scheduler started.")
