import telebot
import os
import time
import requests
from telebot import types

# Use environment variables for security
bot_token = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(bot_token)

# Bot for storing user details
STORAGE_BOT_TOKEN = os.getenv('STORAGE_BOT_TOKEN')
storage_bot = telebot.TeleBot(STORAGE_BOT_TOKEN)
STORAGE_BOT_CHAT_ID = os.getenv('STORAGE_BOT_CHAT_ID')

# File to store registered users
REGISTERED_USERS_FILE = 'registered_users.txt'
LOG_FILE = 'user_logs.txt'

# Function to load registered users
def load_registered_users():
    if os.path.exists(REGISTERED_USERS_FILE):
        with open(REGISTERED_USERS_FILE, 'r') as file:
            return set(line.strip() for line in file)
    return set()

# Function to save registered users
def save_registered_users(users):
    with open(REGISTERED_USERS_FILE, 'w') as file:
        for user in users:
            file.write(user + '\n')

# Function to log user activity
def log_user_activity(user_id, username, command, details):
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(f"{int(time.time())} - {user_id} - {username} - {command} - {details}\n")

# Function to send logs to another bot
def send_log_to_storage_bot(user_id, username, command, details):
    message = f"User ID: {user_id}\nUsername: {username}\nCommand: {command}\nDetails: {details}"
    storage_bot.send_message(STORAGE_BOT_CHAT_ID, message)

# Initialize registered users
registered_users = load_registered_users()

# Define the owner IDs
OWNER_IDS = ['5938629062', '1984816095']

# Command: /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Welcome to the BITTU CHECKER Bot! Use /help to see available commands.")

# Command: /help
@bot.message_handler(commands=['help'])
def help(message):
    help_text = """
    Available Commands:
    /scr username limit - Scrape CCs for the given username and limit
    /chk - Check CCs for Luhn validity
    /register - Register yourself to use commands
    /checkcombo - Check if the scraped CC combo file is valid
    /registered - List registered user IDs (owner only)
    """
    bot.send_message(message.chat.id, help_text)

# Command: /scr - Scrape CCs
@bot.message_handler(commands=['scr'])
def scrape_ccs(message):
    if str(message.from_user.id) not in registered_users and str(message.from_user.id) not in OWNER_IDS:
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    chat_id = message.chat.id
    args = message.text.split()

    if len(args) < 3:
        bot.send_message(chat_id, "Please provide both username and limit. Usage: /scr username limit")
        return

    username = args[1]
    limit = args[2]
    
    start_time = time.time()
    msg = bot.send_message(chat_id, 'Scraping...')

    try:
        response = requests.get(f'https://scrd-3c14ab273e76.herokuapp.com/scr', 
                                params={'username': username, 'limit': limit}, timeout=120)
        raw = response.json()

        if 'error' in raw:
            bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=f"Error: {raw['error']}")
            log_user_activity(message.from_user.id, message.from_user.username, '/scr', f"Error: {raw['error']}")
            send_log_to_storage_bot(message.from_user.id, message.from_user.username, '/scr', f"Error: {raw['error']}")
        else:
            cards = raw['cards']
            found = str(raw['found'])
            file = f'x{found}_Scrapped_by_BITTU_CHECKER.txt'
            
            if cards:
                with open(file, "w") as f:
                    f.write(cards)
                with open(file, "rb") as f:
                    bot.delete_message(chat_id=chat_id, message_id=msg.message_id)
                    end_time = time.time()
                    time_taken = end_time - start_time
                    cap = f'<b>Scraped Successfully ✅\nTarget -» <code>{str(username)}</code>\nFound -» <code>{found}</code>\nTime Taken -» <code>{time_taken:.2f} seconds</code>\nREQ BY -» <code>{message.from_user.first_name}</code></b>'
                    bot.send_document(chat_id=message.chat.id, document=f, caption=cap, parse_mode='HTML')
                try:
                    os.remove(file)
                except PermissionError as e:
                    bot.send_message(chat_id, f"Error deleting file: {e}")
                log_user_activity(message.from_user.id, message.from_user.username, '/scr', f"Target: {username}, Found: {found}")
                send_log_to_storage_bot(message.from_user.id, message.from_user.username, '/scr', f"Target: {username}, Found: {found}")
            else:
                bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text="No cards found.")
                log_user_activity(message.from_user.id, message.from_user.username, '/scr', "No cards found.")
                send_log_to_storage_bot(message.from_user.id, message.from_user.username, '/scr', "No cards found.")
    
    except requests.exceptions.RequestException as e:
        bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=f"Request error: {e}")
        log_user_activity(message.from_user.id, message.from_user.username, '/scr', f"Request error: {e}")
        send_log_to_storage_bot(message.from_user.id, message.from_user.username, '/scr', f"Request error: {e}")
    except Exception as e:
        bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=f"An error occurred: {e}")
        log_user_activity(message.from_user.id, message.from_user.username, '/scr', f"An error occurred: {e}")
        send_log_to_storage_bot(message.from_user.id, message.from_user.username, '/scr', f"An error occurred: {e}")

# Command: /chk - Luhn validation
@bot.message_handler(commands=['chk'])
def chk_command(message):
    if str(message.from_user.id) not in registered_users and str(message.from_user.id) not in OWNER_IDS:
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    msg = bot.reply_to(message, "Send me the CC file.")
    bot.register_next_step_handler(msg, process_file)

def process_file(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save the uploaded file locally
        combo_file = f'combo_{int(time.time())}.txt'
        with open(combo_file, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        tim = str(int(time.time()))
        pass_file = f'pass_luhn_GoodCard{tim}.txt'
        fail_file = f'fail_luhn_BadCard{tim}.txt'
        
        check(combo_file, pass_file, fail_file)

        # Send results back to the user
        with open(pass_file, 'rb') as pf:
            bot.send_document(message.chat.id, pf, caption="Valid CCs (Passed Luhn Check)")

        with open(fail_file, 'rb') as ff:
            bot.send_document(message.chat.id, ff, caption="Invalid CCs (Failed Luhn Check)")

        # Clean up local files
        os.remove(combo_file)
        os.remove(pass_file)
        os.remove(fail_file)
        log_user_activity(message.from_user.id, message.from_user.username, '/chk', "Checked CC file")
        send_log_to_storage_bot(message.from_user.id, message.from_user.username, '/chk', "Checked CC file")
    
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")
        log_user_activity(message.from_user.id, message.from_user.username, '/chk', f"An error occurred: {e}")
        send_log_to_storage_bot(message.from_user.id, message.from_user.username, '/chk', f"An error occurred: {e}")

# Command: /checkcombo - Check if scraped combo file is valid
@bot.message_handler(commands=['checkcombo'])
def check_combo_command(message):
    if str(message.from_user.id) not in registered_users and str(message.from_user.id) not in OWNER_IDS:
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    msg = bot.reply_to(message, "Send me the scraped combo file.")
    bot.register_next_step_handler(msg, process_scraped_combo)

def process_scraped_combo(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save the uploaded file locally
        combo_file = f'scraped_combo
