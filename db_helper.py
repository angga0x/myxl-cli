import sqlite3

def init_db():
    conn = sqlite3.connect('myxl_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            phone_number TEXT UNIQUE,
            refresh_token TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_or_update_user(user_id, phone_number, refresh_token):
    conn = sqlite3.connect('myxl_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, phone_number, refresh_token)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
        phone_number = excluded.phone_number,
        refresh_token = excluded.refresh_token
    ''', (user_id, phone_number, refresh_token))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('myxl_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"user_id": user[0], "phone_number": user[1], "refresh_token": user[2]}
    return None

def remove_user(user_id):
    conn = sqlite3.connect('myxl_bot.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def count_users():
    conn = sqlite3.connect('myxl_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count

# Initialize the database when the module is imported
init_db()
