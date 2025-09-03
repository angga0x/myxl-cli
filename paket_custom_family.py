import json
from api_request import send_api_request, get_family, purchase_package
from auth_helper import AuthInstance
from ui import clear_screen, pause, show_package_details
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import redis_helper

def get_packages_by_family(family_code: str, user_id: int):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_tokens(user_id)
    if not tokens:
        print("No active user tokens found.")
        return None
    
    data = get_family(api_key, tokens, family_code)
    if not data:
        print("Failed to load family data.")
        return None
        
    return data

async def get_packages_by_family_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE, family_code: str):
    user_id = update.message.from_user.id
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_tokens(user_id)
    if not tokens:
        await update.message.reply_text("No active user tokens found.")
        return

    data = get_packages_by_family(family_code, user_id)
    if not data or 'package_variants' not in data:
        await update.message.reply_text("Failed to load family data or no package variants found.")
        return

    packages_list = []
    keyboard = []
    family_name = data.get('package_family', {}).get('name', 'Unknown Family')
    message = f"Paket Tersedia untuk Family {family_name}:\n"
    
    packages_list = []
    keyboard = []
    pkg_index = 0
    for variant in data["package_variants"]:
        variant_name = variant.get("name", "N/A")
        message += f"\n*{variant_name}*\n"
        row = []
        for option in variant.get("package_options", []):
            code = option.get('package_option_code')
            if code:
                packages_list.append(option)
                button_text = f"{option.get('name', 'N/A')} - Rp {option.get('price', 0)}"
                button = InlineKeyboardButton(button_text, callback_data=f"fam_{pkg_index}")
                row.append(button)
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
                pkg_index += 1
        if row:
            keyboard.append(row)

    keyboard.append([InlineKeyboardButton("Kembali ke Menu Utama", callback_data='main_menu')])
    
    if not keyboard:
        await update.message.reply_text("Tidak ada paket valid yang ditemukan.")
        return

    # Store the detailed package list in redis
    redis_helper.set_data(f"family_packages_{user_id}", packages_list)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')

async def purchase_package_from_family_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    callback_data = query.data
    user_id = query.from_user.id

    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_tokens(user_id)
    if not tokens:
        await query.edit_message_text("No active user tokens found.")
        return

    # Check if this is a confirmation callback
    if callback_data.startswith('fam_confirm_'):
        try:
            pkg_index = int(callback_data.split('_')[2])
            packages_list = redis_helper.get_data(f"family_packages_{user_id}")
            if packages_list and 0 <= pkg_index < len(packages_list):
                selected_package = packages_list[pkg_index]
                package_code = selected_package.get('package_option_code')
                package_name = selected_package.get('name', 'N/A')

                await query.edit_message_text(f"Membeli paket: {package_name} dengan QRIS...")
                purchase_result = purchase_package(api_key, tokens, package_code, payment_method="QRIS")
                
                if isinstance(purchase_result, str) and purchase_result.endswith('.png'):
                    img_path = purchase_result
                    await query.message.reply_photo(photo=open(img_path, 'rb'), caption="Silakan scan QRIS ini untuk menyelesaikan pembayaran.")
                    await query.edit_message_text("QRIS telah dikirim.")
                elif isinstance(purchase_result, dict) and 'message' in purchase_result:
                    await query.edit_message_text(f"Gagal: {purchase_result['message']}")
                else:
                    await query.edit_message_text("Gagal membuat QRIS.")
            else:
                await query.edit_message_text("Pilihan paket tidak valid.")
        except (ValueError, IndexError):
            await query.edit_message_text("Terjadi kesalahan saat memproses pilihan Anda.")
        
        # The conversation ends here, and the user can scroll up to the main menu
        return

    # If not a confirmation, it's the initial package selection
    elif callback_data.startswith('fam_'):
        try:
            pkg_index = int(callback_data.split('_')[1])
            packages_list = redis_helper.get_data(f"family_packages_{user_id}")
            if packages_list and 0 <= pkg_index < len(packages_list):
                selected_package = packages_list[pkg_index]
                package_name = selected_package.get('name', 'N/A')
                package_price = selected_package.get('price', 0)

                confirmation_text = (
                    f"Anda akan membeli paket:\n"
                    f"Nama: {package_name}\n"
                    f"Harga: Rp {package_price}\n\n"
                    f"Metode pembayaran default adalah QRIS. Lanjutkan?"
                )
                keyboard = [
                    [
                        InlineKeyboardButton("Ya, Lanjutkan", callback_data=f"fam_confirm_{pkg_index}"),
                        InlineKeyboardButton("Batal", callback_data='cancel_purchase')
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text=confirmation_text, reply_markup=reply_markup)
            else:
                await query.edit_message_text("Pilihan paket tidak valid.")
        except (ValueError, IndexError):
            await query.edit_message_text("Terjadi kesalahan saat memproses pilihan Anda.")

    elif callback_data == 'cancel_purchase':
        await query.edit_message_text("Pembelian dibatalkan.")
        # The conversation ends here, and the user can scroll up to the main menu
        return

    elif callback_data == 'main_menu':
        from telegram_bot import show_main_menu_telegram, MENU
        await show_main_menu_telegram(update, context)
        return MENU
