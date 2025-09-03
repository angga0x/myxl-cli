# MyXL CLI Client

# How to get API Key
Chat telegram bot [@fykxt_bot](https://t.me/fykxt_bot) with message `/viewkey`. Copy the API key.

# How to run with TERMUX
1. Update & Upgrade Termux
```
apt update && apt full-upgrade
```
2. Install Git
```
pkg install git
```
3. Install Python
```
pkg install python
```
4. Clone this repo
```
git clone https://github.com/flyxt/myxl-cli
```
5. Open the folder
```
cd myxl-cli
```
6. Install dependencies
```
pip install -r requirements.txt
```
7. Run the script
```
python main.py
```
8. Input your API key when prompted

# How to run the Telegram Bot
1.  **Create a `.env` file:**
    Create a file named `.env` in the root of the project and add the following content:
    ```
    TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
    REDIS_HOST=your_redis_host
    REDIS_PORT=your_redis_port
    REDIS_PASSWORD=your_redis_password
    ```
    Replace the placeholder values with your actual Telegram Bot Token and Redis credentials.

2.  **Install dependencies:**
    ```
    pip install -r requirements.txt
    ```
3.  **Run the bot:**
    ```
    python telegram_bot.py
    ```
4.  **Start a chat:**
    Open Telegram and start a chat with your bot.
