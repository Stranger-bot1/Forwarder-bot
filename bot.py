from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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

# Web Server for UptimeRobot
@app_web.route('/')
def home():
    return "Bot is Running!"

def run_web():
    app_web.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()

# User Dashboard
@bot.on_message(filters.command("start"))
async def start(client, message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id not in data:
        data[user_id] = {"sources": [], "targets": [], "filters": {"text": True, "photo": True, "video": True, "document": True}}
        save_data(data)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 My Sources", callback_data=f"sources_{user_id}")],
        [InlineKeyboardButton("🎯 My Targets", callback_data=f"targets_{user_id}")],
        [InlineKeyboardButton("⚙️ My Filters", callback_data=f"filters_{user_id}")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ])
    await message.reply("👋 Welcome to your Auto Forwarder Dashboard!", reply_markup=keyboard)

# Manage Sources
@bot.on_callback_query(filters.regex(r'sources_(\d+)'))
async def sources_menu(client, callback_query):
    user_id = callback_query.matches[0].group(1)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Source", callback_data=f"add_source_{user_id}")],
        [InlineKeyboardButton("📂 View Sources", callback_data=f"view_sources_{user_id}")],
        [InlineKeyboardButton("❌ Remove Source", callback_data=f"remove_source_{user_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_dashboard")]
    ])
    await callback_query.message.edit_text("Manage your Source Channels:", reply_markup=keyboard)

# Manage Targets
@bot.on_callback_query(filters.regex(r'targets_(\d+)'))
async def targets_menu(client, callback_query):
    user_id = callback_query.matches[0].group(1)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Target", callback_data=f"add_target_{user_id}")],
        [InlineKeyboardButton("📂 View Targets", callback_data=f"view_targets_{user_id}")],
        [InlineKeyboardButton("❌ Remove Target", callback_data=f"remove_target_{user_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_dashboard")]
    ])
    await callback_query.message.edit_text("Manage your Target Channels:", reply_markup=keyboard)

# Back to Dashboard
@bot.on_callback_query(filters.regex("back_to_dashboard"))
async def back_to_dashboard(client, callback_query):
    await start(client, callback_query.message)

# Add Source
@bot.on_callback_query(filters.regex(r'add_source_(\d+)'))
async def add_source(client, callback_query):
    user_id = callback_query.matches[0].group(1)
    await callback_query.message.edit_text("Please send the @username or channel ID of the source channel.")

    @bot.on_message(filters.private & filters.text)
    async def get_source(client, message):
        data = load_data()
        source = message.text.strip()
        if source not in data[user_id]['sources']:
            data[user_id]['sources'].append(source)
            save_data(data)
            await message.reply(f"✅ Source channel {source} added successfully.")
        else:
            await message.reply("⚠️ This source channel is already added.")

# Add Target
@bot.on_callback_query(filters.regex(r'add_target_(\d+)'))
async def add_target(client, callback_query):
    user_id = callback_query.matches[0].group(1)
    await callback_query.message.edit_text("Please send the @username or channel ID of the target channel.")

    @bot.on_message(filters.private & filters.text)
    async def get_target(client, message):
        data = load_data()
        target = message.text.strip()
        if target not in data[user_id]['targets']:
            data[user_id]['targets'].append(target)
            save_data(data)
            await message.reply(f"✅ Target channel {target} added successfully.")
        else:
            await message.reply("⚠️ This target channel is already added.")

# View Sources
@bot.on_callback_query(filters.regex(r'view_sources_(\d+)'))
async def view_sources(client, callback_query):
    user_id = callback_query.matches[0].group(1)
    data = load_data()
    sources = "\n".join(data[user_id]['sources']) if data[user_id]['sources'] else "No source channels added."
    await callback_query.message.edit_text(f"📂 Source Channels:\n{sources}")

# View Targets
@bot.on_callback_query(filters.regex(r'view_targets_(\d+)'))
async def view_targets(client, callback_query):
    user_id = callback_query.matches[0].group(1)
    data = load_data()
    targets = "\n".join(data[user_id]['targets']) if data[user_id]['targets'] else "No target channels added."
    await callback_query.message.edit_text(f"🎯 Target Channels:\n{targets}")

# Remove Source
@bot.on_callback_query(filters.regex(r'remove_source_(\d+)'))
async def remove_source(client, callback_query):
    user_id = callback_query.matches[0].group(1)
    await callback_query.message.edit_text("Please send the @username or channel ID of the source channel to remove.")

    @bot.on_message(filters.private & filters.text)
    async def delete_source(client, message):
        data = load_data()
        source = message.text.strip()
        if source in data[user_id]['sources']:
            data[user_id]['sources'].remove(source)
            save_data(data)
            await message.reply(f"✅ Source channel {source} removed successfully.")
        else:
            await message.reply("⚠️ Source channel not found.")

# Remove Target
@bot.on_callback_query(filters.regex(r'remove_target_(\d+)'))
async def remove_target(client, callback_query):
    user_id = callback_query.matches[0].group(1)
    await callback_query.message.edit_text("Please send the @username or channel ID of the target channel to remove.")

    @bot.on_message(filters.private & filters.text)
    async def delete_target(client, message):
        data = load_data()
        target = message.text.strip()
        if target in data[user_id]['targets']:
            data[user_id]['targets'].remove(target)
            save_data(data)
            await message.reply(f"✅ Target channel {target} removed successfully.")
        else:
            await message.reply("⚠️ Target channel not found.")

# Filters Menu
@bot.on_callback_query(filters.regex(r'filters_(\d+)'))
async def filters_menu(client, callback_query):
    user_id = callback_query.matches[0].group(1)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Text", callback_data=f"filter_text_{user_id}"),
         InlineKeyboardButton("🖼️ Photo", callback_data=f"filter_photo_{user_id}")],
        [InlineKeyboardButton("🎥 Video", callback_data=f"filter_video_{user_id}"),
         InlineKeyboardButton("📄 Document", callback_data=f"filter_document_{user_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_dashboard")]
    ])
    await callback_query.message.edit_text("Select message types to forward:", reply_markup=keyboard)

# Toggle Filters
@bot.on_callback_query(filters.regex(r'filter_(\w+)_(\d+)'))
async def toggle_filter(client, callback_query):
    filter_type = callback_query.matches[0].group(1)
    user_id = callback_query.matches[0].group(2)

    data = load_data()
    current = data[user_id]['filters'].get(filter_type, True)
    data[user_id]['filters'][filter_type] = not current
    save_data(data)
    status = "✅ Enabled" if not current else "❌ Disabled"
    await callback_query.answer(f"{filter_type.capitalize()} {status}")

# Help Section
@bot.on_callback_query(filters.regex("help"))
async def help_message(client, callback_query):
    await callback_query.message.edit_text(
        "ℹ️ **Bot Instructions:**\n"
        "- Add source and target channels.\n"
        "- Set which types of messages you want to forward.\n"
        "- Bot must be **admin** in both channels.\n"
        "- This bot will copy messages (no forwarded tag).\n"
        "- Detailed error messages will be sent to you directly.\n"
        "- Enjoy your personal forwarding dashboard! 🚀"
    )

# Forwarding Messages (Multi-User Aware)
@bot.on_message(filters.group | filters.channel)
async def forward_message(client, message):
    data = load_data()
    for user_id, user_data in data.items():
        if message.chat.username in user_data['sources']:
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

keep_alive()
bot.run()
