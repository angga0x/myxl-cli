import json
from api_request import send_api_request, get_family, purchase_package
from auth_helper import AuthInstance
from ui import pause
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import redis_helper

PACKAGE_FAMILY_CODE = "08a3b1e6-8e78-4e45-a540-b40f06871cfe"

def get_package_xut(user_id):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_tokens(user_id)
    if not tokens:
        print("No active user tokens found.")
        pause()
        return None
    
    packages = []
    
    data = get_family(api_key, tokens, PACKAGE_FAMILY_CODE)
    package_variants = data["package_variants"]
    start_number = 1
    for variant in package_variants:
        for option in variant["package_options"]:
            friendly_name = option["name"]
            
            if friendly_name.lower() == "vidio":
                friendly_name = "Unli Turbo Vidio"
            if friendly_name.lower() == "iflix":
                friendly_name = "Unli Turbo Iflix"
                
            packages.append({
                "number": start_number,
                "name": friendly_name,
                "price": option["price"],
                "code": option["package_option_code"]
            })
            
            start_number += 1
    return packages

async def get_package_xut_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_tokens(user_id)
    if not tokens:
        await query.edit_message_text("No active user tokens found.")
        return

    packages = get_package_xut(user_id)
    
    if packages:
        keyboard = []
        row = []
        pkg_index = 0
        for package in packages:
            if package.get('code'):
                button_text = f"{package['name']} - Rp {package['price']}"
                button = InlineKeyboardButton(button_text, callback_data=f"xut_{pkg_index}")
                row.append(button)
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
                pkg_index += 1
        if row:
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton("Kembali ke Menu Utama", callback_data='main_menu')])
        
        if not keyboard:
            await query.edit_message_text("Tidak ada paket valid yang ditemukan.")
            return
        
        redis_helper.set_data(f"xut_packages_{user_id}", packages)
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Pilih paket XUT:", reply_markup=reply_markup)
    else:
        await query.edit_message_text("Gagal mengambil daftar paket XUT.")

async def purchase_xut_package_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    if callback_data.startswith('xut_confirm_'):
        try:
            pkg_index = int(callback_data.split('_')[2])
            packages_list = redis_helper.get_data(f"xut_packages_{user_id}")
            if packages_list and 0 <= pkg_index < len(packages_list):
                selected_package = packages_list[pkg_index]
                package_code = selected_package.get('code')
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
    elif callback_data.startswith('xut_'):
        try:
            pkg_index = int(callback_data.split('_')[1])
            packages_list = redis_helper.get_data(f"xut_packages_{user_id}")
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
                        InlineKeyboardButton("Ya, Lanjutkan", callback_data=f"xut_confirm_{pkg_index}"),
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
