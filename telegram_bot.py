import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from api_request import get_otp, submit_otp, get_balance
from auth_helper import AuthInstance
from datetime import datetime
# The following modules will be created/modified in the next steps
from my_package import fetch_my_packages_telegram
from paket_xut import get_package_xut_telegram, purchase_xut_package_telegram
from paket_custom_family import get_packages_by_family_telegram, purchase_package_from_family_telegram
import reporting
import redis_helper
import os
from dotenv import load_dotenv

load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define the states
PHONE_NUMBER, OTP, MENU, FAMILY_CODE, XUT_PURCHASE, FAMILY_PURCHASE = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation, checks for auto-login, or asks for phone number."""
    user_id = update.message.from_user.id
    session = AuthInstance.get_session(user_id)
    if session:
        await update.message.reply_text(f"Selamat datang kembali, {session['number']}!")
        await show_main_menu_telegram(update, context)
        return MENU
    else:
        await update.message.reply_text(
            "Hai! Selamat datang di bot MyXL. "
            "Silakan masukkan nomor telepon Anda (contoh: 62878xxxxxxx)."
        )
        return PHONE_NUMBER


async def show_main_menu_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE, send_new=False):
    user_id = update.effective_user.id
    session = AuthInstance.get_session(user_id)
    if not session:
        # Handle case where there is no active user
        if update.callback_query:
            await update.callback_query.edit_message_text("Sesi tidak ditemukan. Silakan /start lagi.")
        else:
            await update.message.reply_text("Sesi tidak ditemukan. Silakan /start lagi.")
        return

    loading_message = await update.effective_message.reply_text("Fetching balance...")
    balance_data = get_balance(AuthInstance.api_key, session["tokens"]["id_token"])
    balance_remaining = balance_data.get("remaining", 0)
    balance_expired_at_ts = balance_data.get("expired_at")
    
    balance_str = f"Rp {balance_remaining:,}".replace(',', '.')
    
    expired_at_str = "N/A"
    if balance_expired_at_ts:
        expired_at_str = datetime.fromtimestamp(balance_expired_at_ts).strftime('%d %B %Y')

    message = (
        f"Nomor: {session['number']}\n"
        f"Sisa pulsa: {balance_str}\n"
        f"Masa aktif: {expired_at_str}"
    )
    
    keyboard = [
        [InlineKeyboardButton("Ganti Akun", callback_data='switch_account')],
        [InlineKeyboardButton("Cek Kuota Saya", callback_data='check_quota')],
        [InlineKeyboardButton("Beli Paket XUT", callback_data='buy_xut')],
        [InlineKeyboardButton("Beli Paket by Family Code", callback_data='buy_family')],
        [InlineKeyboardButton("Keluar", callback_data='exit')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # If send_new is True, or if there's no callback_query, send a new message.
    # Otherwise, edit the existing one.
    await loading_message.edit_text(text=message, reply_markup=reply_markup)

async def phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the phone number and asks for the OTP."""
    user = update.message.from_user
    user_id = user.id
    phone = update.message.text
    logger.info("Phone number of %s: %s", user.first_name, phone)
    
    redis_helper.set_data(f"phone_{user_id}", phone)
    subscriber_id = get_otp(phone)
    
    if subscriber_id:
        redis_helper.set_data(f"subid_{user_id}", subscriber_id)
        await update.message.reply_text("OTP telah dikirim. Silakan masukkan kode OTP Anda.")
        return OTP
    else:
        keyboard = [[InlineKeyboardButton("Kirim Ulang OTP", callback_data='resend_otp')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Gagal mengirim OTP. Silakan coba lagi.", reply_markup=reply_markup)
        return PHONE_NUMBER


async def otp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the OTP and displays the main menu."""
    user = update.message.from_user
    user_id = user.id
    otp_code = update.message.text
    phone_number = redis_helper.get_data(f"phone_{user_id}")
    logger.info("OTP from %s: %s", user.first_name, otp_code)

    tokens = submit_otp(AuthInstance.api_key, phone_number, otp_code)

    if tokens:
        AuthInstance.login_user(user_id, phone_number, tokens["refresh_token"])
        await update.message.reply_text("Login berhasil!")
        await show_main_menu_telegram(update, context)
        return MENU
    else:
        await update.message.reply_text("OTP salah. Silakan coba lagi.")
        return OTP


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Sampai jumpa lagi!"
    )
    return ConversationHandler.END

async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the user's menu choice from inline keyboard."""
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "switch_account":
        await query.message.reply_text(text="Fitur ganti akun belum diimplementasikan.")
        # The main menu remains, so no need to resend.
        return MENU
    elif choice == "check_quota":
        await fetch_my_packages_telegram(update, context)
        # The user gets the quota info in a new message and can scroll up to the menu.
        return MENU
    elif choice == "buy_xut":
        await get_package_xut_telegram(update, context)
        return XUT_PURCHASE
    elif choice == "buy_family":
        await query.edit_message_text("Masukkan family code:")
        return FAMILY_CODE
    elif choice == "exit":
        keyboard = [
            [
                InlineKeyboardButton("Ya", callback_data='confirm_exit_yes'),
                InlineKeyboardButton("Tidak", callback_data='confirm_exit_no')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Apakah Anda yakin ingin keluar?", reply_markup=reply_markup)
        return MENU
    else:
        await query.edit_message_text(text="Pilihan tidak valid.")
        return MENU

async def confirm_exit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the exit confirmation."""
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == 'confirm_exit_yes':
        user_id = query.from_user.id
        AuthInstance.logout_user(user_id)
        await query.edit_message_text("Anda telah keluar. Sampai jumpa lagi!")
        return ConversationHandler.END
    else:
        await show_main_menu_telegram(update, context)
        return MENU

async def handle_family_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the family code input."""
    family_code = update.message.text
    await get_packages_by_family_telegram(update, context, family_code)
    return FAMILY_PURCHASE

async def resend_otp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Resends the OTP."""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    phone_number = redis_helper.get_data(f"phone_{user_id}")
    if phone_number:
        otp_result = get_otp(phone_number)
        if isinstance(otp_result, str):  # Success case
            redis_helper.set_data(f"subid_{user_id}", otp_result)
            await query.edit_message_text("OTP telah dikirim ulang. Silakan masukkan kode OTP Anda.")
            return OTP
        elif isinstance(otp_result, dict) and "error" in otp_result:
            # Time limit error
            await query.message.reply_text(otp_result["error"])
            return PHONE_NUMBER # Stay in the same state
        else:
            # Other errors
            await query.edit_message_text("Gagal mengirim ulang OTP. Silakan coba lagi nanti.")
            return PHONE_NUMBER
    else:
        await query.edit_message_text("Nomor telepon tidak ditemukan. Silakan /start lagi.")
        return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Start the reporting scheduler
    reporting.start_scheduler(application)

    # Add conversation handler with the states PHONE_NUMBER, OTP, MENU and FAMILY_CODE
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE_NUMBER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, phone_number),
                CallbackQueryHandler(resend_otp, pattern='^resend_otp$')
            ],
            OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, otp)],
            MENU: [
                CallbackQueryHandler(handle_menu_choice, pattern='^(switch_account|check_quota|buy_xut|buy_family|exit)$'),
                CallbackQueryHandler(confirm_exit, pattern='^confirm_exit_')
            ],
            FAMILY_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_family_code)],
            XUT_PURCHASE: [CallbackQueryHandler(purchase_xut_package_telegram)],
            FAMILY_PURCHASE: [CallbackQueryHandler(purchase_package_from_family_telegram)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
