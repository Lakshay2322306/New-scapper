import telebot
import os
import time
import requests
from telebot import types

# Enter bot token here
bot_token = os.getenv('BOT_TOKEN')  # Use environment variables for security
bot = telebot.TeleBot(bot_token)

# Define the owner ID (for command restriction)
OWNER_ID = 'YOUR_OWNER_TELEGRAM_ID'

# Command: /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Welcome to the CC Scraper Bot! Use /help to see available commands.")

# Command: /help
@bot.message_handler(commands=['help'])
def help(message):
    help_text = """
    Available Commands:
    /scr username limit - Scrape CCs for the given username and limit
    /luhncheck - Check CCs for Luhn validity (owner only)
    /register - Register new commands (owner only)
    """
    bot.send_message(message.chat.id, help_text)

# Command: /scr - Scrape CCs
@bot.message_handler(commands=['scr'])
def scrape_ccs(message):
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
        else:
            cards = raw['cards']
            found = str(raw['found'])
            file = f'x{found}_Scrapped_by_@XAY4N.txt'
            
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
            else:
                bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text="No cards found.")
    
    except requests.exceptions.RequestException as e:
        bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=f"Request error: {e}")
    except Exception as e:
        bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=f"An error occurred: {e}")

# Command: /luhncheck - Luhn validation (Owner only)
@bot.message_handler(commands=['luhncheck'])
def luhncheck_command(message):
    if str(message.from_user.id) != OWNER_ID:
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
    
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

# Luhn check logic
def luhn_check(cc):
    cc = cc.replace(' ', '')
    total = 0
    cc_reversed = cc[::-1]

    for i, digit in enumerate(cc_reversed):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n

    return total % 10 == 0

def check(main_file, pass_file, fail_file):
    try:
        with open(main_file, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print("File not found. Please try again.")
        return

    with open(pass_file, 'w') as pass_f, open(fail_file, 'w') as fail_f:
        for line in lines:
            parts = line.split('|')
            if len(parts) > 0:
                cc_number = parts[0].strip()
                if luhn_check(cc_number):
                    pass_f.write(line)
                else:
                    fail_f.write(line)

# Command: /register - Owner only command
@bot.message_handler(commands=['register'])
def register_command(message):
    if str(message.from_user.id) != OWNER_ID:
        bot.reply_to(message, "You are not authorized to use this command.")
        return
    bot.send_message(message.chat.id, "You have been registered to execute advanced commands.")

# Polling loop
bot.polling()
