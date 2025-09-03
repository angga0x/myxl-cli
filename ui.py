import json
import os
import sys
from datetime import datetime
from api_request import get_otp, submit_otp, save_tokens, get_package, purchase_package
from purchase_api import show_multipayment, show_qris_payment, settlement_bounty

def clear_screen():
    print("clearing screen...")
    os.system('cls' if os.name == 'nt' else 'clear')

def pause():
    input("\nTekan Enter untuk lanjut...")
    
def show_banner():
    print("--------------------------")
    print("Dor XL by Flyxt9")
    print("--------------------------")
    
def show_main_menu(number, balance, balance_expired_at):
    clear_screen()
    phone_number = number
    remaining_balance = balance
    expired_at = balance_expired_at
    expired_at_dt = datetime.fromtimestamp(expired_at).strftime("%Y-%m-%d %H:%M:%S")
    
    print("--------------------------")
    print("Informasi Akun")
    print(f"Nomor: {phone_number}")
    print(f"Pulsa: Rp {remaining_balance}")
    print(f"Masa aktif: {expired_at_dt}")
    print("--------------------------")
    print("Menu:")
    print("1. Login/Ganti akun")
    print("2. Lihat Paket Saya")
    print("3. Beli Paket XUT")
    print("4. Beli Paket Berdasarkan Family Code")
    print("99. Tutup aplikasi")
    print("--------------------------")
        
def show_account_menu():
    from auth_helper import AuthInstance
    clear_screen()
    AuthInstance.load_tokens()
    users = AuthInstance.refresh_tokens
    active_user = AuthInstance.get_active_user()
    
    # print(f"users: {users}")
    
    in_account_menu = True
    add_user = False
    while in_account_menu:
        clear_screen()
        print("--------------------------")
        if AuthInstance.get_active_user() is None or add_user:
            number, refresh_token = login_prompt(AuthInstance.api_key)
            if not refresh_token:
                print("Gagal menambah akun. Silahkan coba lagi.")
                pause()
                continue
            
            AuthInstance.add_refresh_token(int(number), refresh_token)
            AuthInstance.load_tokens()
            users = AuthInstance.refresh_tokens
            
            
            if add_user:
                add_user = False
            continue
        
        print("Akun Tersimpan:")
        if not users or len(users) == 0:
            print("Tidak ada akun tersimpan.")

        for idx, user in enumerate(users):
            is_active = active_user and user["number"] == active_user["number"]
            active_marker = " (Aktif)" if is_active else ""
            print(f"{idx + 1}. {user['number']}{active_marker}")
        
        print("Command:")
        print("0: Tambah Akun")
        print("00: Kembali ke menu utama")
        print("99: Hapus Akun aktif")
        print("Masukan nomor akun untuk berganti.")
        input_str = input("Pilihan:")
        if input_str == "00":
            in_account_menu = False
            return active_user["number"] if active_user else None
        elif input_str == "0":
            add_user = True
            continue
        elif input_str == "99":
            if not active_user:
                print("Tidak ada akun aktif untuk dihapus.")
                pause()
                continue
            confirm = input(f"Yakin ingin menghapus akun {active_user['number']}? (y/n): ")
            if confirm.lower() == 'y':
                AuthInstance.remove_refresh_token(active_user["number"])
                # AuthInstance.load_tokens()
                users = AuthInstance.refresh_tokens
                active_user = AuthInstance.get_active_user()
                print("Akun berhasil dihapus.")
                pause()
            else:
                print("Penghapusan akun dibatalkan.")
                pause()
            continue
        elif input_str.isdigit() and 1 <= int(input_str) <= len(users):
            selected_user = users[int(input_str) - 1]
            return selected_user['number']
        else:
            print("Input tidak valid. Silahkan coba lagi.")
            pause()
            continue
        
def show_login_menu():
    clear_screen()
    print("--------------------------")
    print("Login ke MyXL")
    print("--------------------------")
    print("1. Request OTP")
    print("2. Submit OTP")
    print("99. Tutup aplikasi")
    print("--------------------------")
    
def login_prompt(api_key: str):
    clear_screen()
    print("--------------------------")
    print("Login ke MyXL")
    print("--------------------------")
    print("Masukan nomor XL Prabayar (Contoh 6281234567890):")
    phone_number = input("Nomor: ")

    if not phone_number.startswith("628") or len(phone_number) < 10 or len(phone_number) > 14:
        print("Nomor tidak valid. Pastikan nomor diawali dengan '628' dan memiliki panjang yang benar.")
        return None

    try:
        subscriber_id = get_otp(phone_number)
        if not subscriber_id:
            return None
        print("OTP Berhasil dikirim ke nomor Anda.")
        
        otp = input("Masukkan OTP yang telah dikirim: ")
        if not otp.isdigit() or len(otp) != 6:
            print("OTP tidak valid. Pastikan OTP terdiri dari 6 digit angka.")
            pause()
            return None
        
        tokens = submit_otp(api_key, phone_number, otp)
        if not tokens:
            print("Gagal login. Periksa OTP dan coba lagi.")
            pause()
            return None
        
        # save_tokens(tokens) #TODO: To remove
        print("Berhasil login!")
        
        return phone_number, tokens["refresh_token"]
    except Exception as e:
        return None, None
    
def show_package_menu(packages):
    from auth_helper import AuthInstance
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print("No active user tokens found.")
        pause()
        return None
    
    in_package_menu = True
    while in_package_menu:
        clear_screen()
        print("--------------------------")
        print("Paket Tersedia")
        print("--------------------------")
        for pkg in packages:
            print(f"{pkg['number']}. {pkg['name']} - Rp {pkg['price']}")
        print("99. Kembali ke menu utama")
        print("--------------------------")
        pkg_choice = input("Pilih paket (nomor): ")
        if pkg_choice == "99":
            in_package_menu = False
            return None
        selected_pkg = next((p for p in packages if p["number"] == int(pkg_choice)), None)
        if not selected_pkg:
            print("Paket tidak ditemukan. Silakan masukan nomor yang benar.")
            continue
        
        is_done = show_package_details(api_key, tokens, selected_pkg["code"])
        if is_done:
            in_package_menu = False
            return None
    
def show_package_details(api_key, tokens, package_option_code):
    clear_screen()
    print("--------------------------")
    print("Detail Paket")
    print("--------------------------")
    package = get_package(api_key, tokens, package_option_code)
    # print(json.dumps(package, indent=2))
    if not package:
        print("Failed to load package details.")
        pause()
        return False
    name2 = package.get("package_detail_variant", "").get("name","") #For Xtra Combo
    price = package["package_option"]["price"]
    detail = package["package_option"]["tnc"]
    detail = detail.replace("<p>", "").replace("</p>", "").replace("<strong>", "").replace("</strong>", "").replace("<br>", "").replace("<br />", "").strip()
    name3 = package.get("package_option", {}).get("name","") #Vidio
    name1 = package.get("package_family", {}).get("name","") #Unlimited Turbo
    
    title = f"{name1} {name2} {name3}".strip()
    
    token_confirmation = package["token_confirmation"]
    ts_to_sign = package["timestamp"]
    payment_for = package["package_family"]["payment_for"]
    

    print(f"Nama: {title}")
    print(f"Harga: Rp {price}")
    print(f"SnK MyXL:\n{detail}")
    print("--------------------------")
    print("1. Beli dengan Pulsa")
    print("2. Beli dengan E-Wallet")
    print("3. Bayar dengan QRIS")
    
    if payment_for == "REDEEM_VOUCHER":
        print("4. Ambil sebagai bonus (jika tersedia)")

    choice = input("Pilih metode pembayaran: ")
    if choice == '1':
        purchase_package(api_key, tokens, package_option_code)
        input("Silahkan cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
        return True
    elif choice == '2':
        show_multipayment(api_key, tokens, package_option_code, token_confirmation, price)
        input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
        return True
    elif choice == '3':
        show_qris_payment(api_key, tokens, package_option_code, token_confirmation, price)
        input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
        return True
    elif choice == '4':
        settlement_bounty(
            api_key=api_key,
            tokens=tokens,
            token_confirmation=token_confirmation,
            ts_to_sign=ts_to_sign,
            payment_target=package_option_code,
            price=price,
            item_name=name2
        )
    else:
        print("Purchase cancelled.")
        return False
    pause()
    sys.exit(0)
