from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_CHAT_ID
import json
import os
from flask import Flask
import threading

app_web = Flask('')

bot = Client("auto_forwarder_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

if not os.path.exists("database.json"):
    with open("database.json", "w") as f:
        json.dump({}, f)


def load_data():
    with open("database.json", "r") as f:
        return json.load(f)


def save_data(data):
    with open("database.json", "w") as f:
        json.dump(data, f, indent=4)


@app_web.route('/')
def home():
    return "Bot is Running!"


def run_web():
    app_web.run(host="0.0.0.0", port=8080)


def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()


@bot.on_message(filters.command("start"))
async def start(client, message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id not in data:
        data[user_id] = {"sources": [], "targets": [], "filters": {"text": True, "photo": True, "video": True, "document": True}, "is_active": True}
        save_data(data)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 My Sources", callback_data=f"sources_{user_id}")],
        [InlineKeyboardButton("🎯 My Targets", callback_data=f"targets_{user_id}")],
        [InlineKeyboardButton("⚙️ My Filters", callback_data=f"filters_{user_id}")],
        [InlineKeyboardButton("▶️ Start Forwarding", callback_data=f"start_{user_id}"), InlineKeyboardButton("⏹️ Stop Forwarding", callback_data=f"stop_{user_id}")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ])
    await message.reply("👋 Welcome to your Auto Forwarder Dashboard!", reply_markup=keyboard)


@bot.on_message(filters.command("checksource"))
async def check_source(client, message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id not in data or not data[user_id]['sources']:
        await message.reply("⚠️ You have no sources added.")
        return

    reply_text = "🔍 Checking sources...\n"
    for source in data[user_id]['sources']:
        try:
            chat = await client.get_chat(source)
            member = await client.get_chat_member(chat.id, 'me')
            reply_text += f"✅ Bot is a member of {source}\n"
        except Exception:
            reply_text += f"❌ Bot is NOT a member of {source}\n"

    await message.reply(reply_text)


@bot.on_message(filters.command("startforwarding"))
async def start_forwarding(client, message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id in data:
        data[user_id]['is_active'] = True
        save_data(data)
        await message.reply("✅ Forwarding started.")
    else:
        await message.reply("⚠️ You have no configuration yet. Please set your sources and targets first.")


@bot.on_message(filters.command("stopforwarding"))
async def stop_forwarding(client, message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id in data:
        data[user_id]['is_active'] = False
        save_data(data)
        await message.reply("⛔ Forwarding stopped.")
    else:
        await message.reply("⚠️ You have no configuration yet.")


@bot.on_callback_query()
async def handle_callbacks(client, callback_query: CallbackQuery):
    data = load_data()
    user_id = str(callback_query.from_user.id)

    if callback_query.data.startswith("start_"):
        if user_id in data:
            data[user_id]['is_active'] = True
            save_data(data)
            await callback_query.answer("✅ Forwarding activated.", show_alert=True)
        else:
            await callback_query.answer("⚠️ No setup found.", show_alert=True)

    elif callback_query.data.startswith("stop_"):
        if user_id in data:
            data[user_id]['is_active'] = False
            save_data(data)
            await callback_query.answer("⏹️ Forwarding deactivated.", show_alert=True)
        else:
            await callback_query.answer("⚠️ No setup found.", show_alert=True)

    elif callback_query.data.startswith("sources_"):
        await callback_query.answer("📂 Source management is under development.", show_alert=True)

    elif callback_query.data.startswith("targets_"):
        await callback_query.answer("🎯 Target management is under development.", show_alert=True)

    elif callback_query.data.startswith("filters_"):
        await callback_query.answer("⚙️ Filter management is under development.", show_alert=True)

    elif callback_query.data == "help":
        await callback_query.answer("ℹ️ Add source/target via commands. Automanage coming soon!", show_alert=True)


@bot.on_message(filters.group | filters.channel)
async def forward_message(client, message):
    data = load_data()
    processed_users = set()

    for user_id, user_data in data.items():
        if not user_data.get('is_active', True):
            continue

        if message.chat.username in user_data['sources'] and user_id not in processed_users:
            try:
                member = await client.get_chat_member(message.chat.id, 'me')
            except Exception:
                await client.send_message(int(user_id), f"❌ Bot is not a member of the source channel: {message.chat.username}")
                continue

            filters_enabled = user_data.get('filters', {})
            allowed = False

            if message.text and filters_enabled.get('text', True):
                allowed = True
            if message.photo and filters_enabled.get('photo', True):
                allowed = True
            if message.video and filters_enabled.get('video', True):
                allowed = True
            if message.document and filters_enabled.get('document', True):
                allowed = True

            if allowed:
                for target in user_data['targets']:
                    try:
                        await message.copy(target)
                    except Exception as e:
                        try:
                            await client.send_message(int(user_id), f"❌ Error forwarding to {target}: {str(e)}")
                        except:
                            pass
                processed_users.add(user_id)


keep_alive()
bot.run()
