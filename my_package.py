from api_request import get_package, send_api_request
from ui import clear_screen, pause
from auth_helper import AuthInstance
from telegram import Update
from telegram.ext import ContextTypes
import json
from datetime import datetime

# Fetch my packages
def fetch_my_packages():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print("No active user tokens found.")
        pause()
        return None
    
    id_token = tokens.get("id_token")
    print("ID Token:", id_token)  # JWT Token
    
    path = "api/v8/packages/quota-details"
    
    payload = {
        "is_enterprise": False,
        "lang": "en",
        "family_member_id": ""
    }
    
    print("Fetching my packages...")
    res = send_api_request(api_key, path, payload, id_token, "POST")
    if res.get("status") != "SUCCESS":
        print("Failed to fetch packages")
        print("Response:", res)
        pause()
        return None
    
    quotas = res["data"]["quotas"]
    
    clear_screen()
    print("===============================")
    print("My Packages")
    print("===============================")
    num = 1
    for quota in quotas:
        quota_code = quota["quota_code"] # Can be used as option_code
        group_code = quota["group_code"]
        name = quota["name"]
        family_code = "N/A"
        
        print(f"fetching package no. {num} details...")
        package_details = get_package(api_key, tokens, quota_code)
        if package_details:
            family_code = package_details["package_family"]["package_family_code"]
        
        print("===============================")
        print(f"Package {num}")
        print(f"Name: {name}")
        print(f"Quota Code: {quota_code}")
        print(f"Family Code: {family_code}")
        print(f"Group Code: {group_code}")
        print("===============================")
        
        num += 1
        
    pause()

async def fetch_my_packages_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    # Use query.message for replies in a callback context
    message_to_reply = query.message

    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_tokens(user_id)
    if not tokens:
        await message_to_reply.reply_text("No active user tokens found.")
        return

    id_token = tokens.get("id_token")
    
    path = "api/v8/packages/quota-details"
    
    payload = {
        "is_enterprise": False,
        "lang": "en",
        "family_member_id": ""
    }
    
    loading_message = await message_to_reply.reply_text("Fetching my packages...")
    res = send_api_request(api_key, path, payload, id_token, "POST")
    if res.get("status") != "SUCCESS":
        await loading_message.edit_text("Failed to fetch packages")
        return

    quotas = res.get("data", {}).get("quotas", [])
    
    if not quotas:
        await loading_message.edit_text("Anda tidak memiliki paket aktif.")
        return

    message_text = "Paket Anda:\n"
    for quota in quotas:
        name = quota.get("name", "N/A")
        group_name = quota.get("group_name", "N/A")
        expired_at_ts = quota.get("expired_at")
        expired_at_str = "N/A"
        if expired_at_ts:
            expired_at_str = datetime.fromtimestamp(expired_at_ts).strftime('%Y-%m-%d %H:%M:%S')

        message_text += "===============================\n"
        message_text += f"Nama: {name}\n"
        message_text += f"Grup: {group_name}\n"
        message_text += f"Berakhir pada: {expired_at_str}\n"
        message_text += "===============================\n"
        
    await loading_message.edit_text(message_text)
