# ADE FX Signal Bot — Fully Automated with USDT TRC20 and NOWPayments
import telebot
import json
import time
import os
import threading
import uuid
import requests
from datetime import datetime, timedelta

API_TOKEN = "7321336997:AAGAKVhFDmFjqjF84lp96moD6d2YuhZw4UE"
CHANNEL_ID = -1002100318005
NOWPAYMENTS_API_KEY = "7JH7P7R-KNDMTCF-QR5TMP3-RZTV2WC"
bot = telebot.TeleBot(API_TOKEN)

ADMIN_USERNAME = "@adedewa001"
SUBSCRIPTION_DAYS = 30
PRICE = "30"
DATA_FILE = "subscriptions.json"
PAYMENTS_FILE = "payment_links.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(PAYMENTS_FILE):
    with open(PAYMENTS_FILE, "w") as f:
        json.dump({}, f)

def load_data(file):
    with open(file, "r") as f:
        return json.load(f)

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, (
        f"Welcome to ADE FX Signals!\n\n"
        f"This is your private access to our premium real-time trading channel.\n"
        f"Subscription: $30 for 30 days\n"
        f"Use /pay to begin or /help to view menu."
    ))

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, (
        "/pay – Start your subscription\n"
        "/status – Check your subscription\n"
        "/renew – Renew your access\n"
        "/help – Show this menu"
    ))

@bot.message_handler(commands=['pay', 'renew'])
def create_payment(message):
    user_id = str(message.from_user.id)
    payment_id = str(uuid.uuid4())[:8]
    url = "https://api.nowpayments.io/v1/invoice"
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "price_amount": 30,
        "price_currency": "usd",
        "order_id": payment_id,
        "pay_currency": "usdttrc20",
        "ipn_callback_url": "https://nowpayments.io",
        "success_url": "https://t.me/adefx_signal_paymentbot",
        "order_description": f"Signal subscription for user {user_id}"
    }
    try:
        r = requests.post(url, json=payload, headers=headers)
        data = r.json()
        invoice_url = data.get("invoice_url")
        if invoice_url:
            payments = load_data(PAYMENTS_FILE)
            payments[payment_id] = {
                "user_id": user_id,
                "username": message.from_user.username or "",
                "created": datetime.now().isoformat()
            }
            save_data(PAYMENTS_FILE, payments)
            bot.reply_to(message, f"To activate your signal access, pay here:\n{invoice_url}")
        else:
            bot.reply_to(message, "Failed to generate payment link. Please try again shortly or contact support.")
    except Exception as e:
        print("Error:", e)
        bot.reply_to(message, "Connection error. Please try again later.")

@bot.message_handler(commands=['status'])
def check_status(message):
    user_id = str(message.from_user.id)
    subs = load_data(DATA_FILE)
    if user_id in subs:
        expiry = datetime.strptime(subs[user_id]["expires"], "%Y-%m-%d")
        if expiry > datetime.now():
            bot.reply_to(message, f"Your subscription is active until {expiry.strftime('%B %d, %Y')}.")
        else:
            bot.reply_to(message, "Your subscription has expired. Use /renew to reactivate.")
    else:
        bot.reply_to(message, "You do not have an active subscription. Use /pay to start.")

def activate_user(user_id, username):
    subs = load_data(DATA_FILE)
    expiry = datetime.now() + timedelta(days=SUBSCRIPTION_DAYS)
    subs[str(user_id)] = {"expires": expiry.strftime("%Y-%m-%d")}
    save_data(DATA_FILE, subs)
    try:
        bot.unban_chat_member(CHANNEL_ID, int(user_id))
        bot.invite_chat_member(CHANNEL_ID, int(user_id))
        bot.send_message(int(user_id), f"✅ Your subscription is now active until {expiry.strftime('%B %d, %Y')}. Welcome to ADE FX!")
        bot.send_message(ADMIN_USERNAME, f"User {username} has been activated until {expiry.strftime('%Y-%m-%d')}.")
    except:
        bot.send_message(ADMIN_USERNAME, f"⚠️ Could not add user {username} ({user_id}) to the channel.")

def monitor_subscriptions():
    while True:
        try:
            subs = load_data(DATA_FILE)
            now = datetime.now()
            for user_id, info in list(subs.items()):
                expiry = datetime.strptime(info["expires"], "%Y-%m-%d")
                days_left = (expiry - now).days
                if days_left == 2:
                    bot.send_message(int(user_id), "Your signal access expires in 2 days. Click /renew to extend.")
                elif expiry < now:
                    try:
                        bot.send_message(int(user_id), "Your subscription has expired. You’ve been removed from the channel.")
                        bot.ban_chat_member(CHANNEL_ID, int(user_id))
                        bot.unban_chat_member(CHANNEL_ID, int(user_id))
                        del subs[user_id]
                    except:
                        continue
            save_data(DATA_FILE, subs)
        except Exception as e:
            print("Monitor error:", e)
        time.sleep(86400)

threading.Thread(target=monitor_subscriptions, daemon=True).start()

print("ADE FX auto-payment bot is now live with USDT TRC20.")
bot.infinity_polling()
