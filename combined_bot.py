from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_CHAT_ID
import json
import os
from flask import Flask
import threading

app_web = Flask('')

bot = Client("auto_forwarder_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

if not os.path.exists("targets.json"):
    with open("targets.json", "w") as f:
        json.dump({"sources": [], "targets": [], "filters": {
            "text": True, "photo": True, "video": True, "document": True}}, f)

def load_data():
    with open("targets.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("targets.json", "w") as f:
        json.dump(data, f, indent=4)

@bot.on_message(filters.command("start"))
async def start(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Manage Sources", callback_data="manage_sources")],
        [InlineKeyboardButton("Manage Targets", callback_data="manage_targets")],
        [InlineKeyboardButton("Set Filters", callback_data="set_filters")],
        [InlineKeyboardButton("Help", callback_data="help")]
    ])
    await message.reply("👋 Welcome to Auto Forwarder Bot!\n\nManage your forwarding settings below.", reply_markup=keyboard)

# MENU NAVIGATION
@bot.on_callback_query(filters.regex("back_to_menu"))
async def back_to_menu(client, callback_query):
    await start(client, callback_query.message)

# MANAGE SOURCES
@bot.on_callback_query(filters.regex("manage_sources"))
async def manage_sources(client, callback_query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Source", callback_data="add_source")],
        [InlineKeyboardButton("📂 View Sources", callback_data="view_sources")],
        [InlineKeyboardButton("❌ Remove Source", callback_data="remove_source")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
    ])
    await callback_query.message.edit_text("Manage your Source Channels:", reply_markup=keyboard)

# MANAGE TARGETS
@bot.on_callback_query(filters.regex("manage_targets"))
async def manage_targets(client, callback_query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Target", callback_data="add_target")],
        [InlineKeyboardButton("📂 View Targets", callback_data="view_targets")],
        [InlineKeyboardButton("❌ Remove Target", callback_data="remove_target")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
    ])
    await callback_query.message.edit_text("Manage your Target Channels:", reply_markup=keyboard)

# ADD SOURCE
@bot.on_callback_query(filters.regex("add_source"))
async def add_source(client, callback_query):
    await callback_query.message.edit_text("Please send the @username or channel ID of the source channel.")

    @bot.on_message(filters.private & filters.text)
    async def get_source(client, message):
        data = load_data()
        source = message.text.strip()
        if source not in data['sources']:
            data['sources'].append(source)
            save_data(data)
            await message.reply(f"✅ Source channel {source} added successfully.")
        else:
            await message.reply("⚠️ This source channel is already added.")

# ADD TARGET
@bot.on_callback_query(filters.regex("add_target"))
async def add_target(client, callback_query):
    await callback_query.message.edit_text("Please send the @username or channel ID of the target channel.")

    @bot.on_message(filters.private & filters.text)
    async def get_target(client, message):
        data = load_data()
        target = message.text.strip()
        if target not in data['targets']:
            data['targets'].append(target)
            save_data(data)
            await message.reply(f"✅ Target channel {target} added successfully.")
        else:
            await message.reply("⚠️ This target channel is already added.")

# VIEW SOURCES
@bot.on_callback_query(filters.regex("view_sources"))
async def view_sources(client, callback_query):
    data = load_data()
    sources = "\n".join(data['sources']) if data['sources'] else "No source channels added."
    await callback_query.message.edit_text(f"📂 Source Channels:\n{sources}")

# VIEW TARGETS
@bot.on_callback_query(filters.regex("view_targets"))
async def view_targets(client, callback_query):
    data = load_data()
    targets = "\n".join(data['targets']) if data['targets'] else "No target channels added."
    await callback_query.message.edit_text(f"🎯 Target Channels:\n{targets}")

# REMOVE SOURCE
@bot.on_callback_query(filters.regex("remove_source"))
async def remove_source(client, callback_query):
    await callback_query.message.edit_text("Please send the @username or channel ID of the source channel to remove.")

    @bot.on_message(filters.private & filters.text)
    async def delete_source(client, message):
        data = load_data()
        source = message.text.strip()
        if source in data['sources']:
            data['sources'].remove(source)
            save_data(data)
            await message.reply(f"✅ Source channel {source} removed successfully.")
        else:
            await message.reply("⚠️ Source channel not found.")

# REMOVE TARGET
@bot.on_callback_query(filters.regex("remove_target"))
async def remove_target(client, callback_query):
    await callback_query.message.edit_text("Please send the @username or channel ID of the target channel to remove.")

    @bot.on_message(filters.private & filters.text)
    async def delete_target(client, message):
        data = load_data()
        target = message.text.strip()
        if target in data['targets']:
            data['targets'].remove(target)
            save_data(data)
            await message.reply(f"✅ Target channel {target} removed successfully.")
        else:
            await message.reply("⚠️ Target channel not found.")

# SET FILTERS
@bot.on_callback_query(filters.regex("set_filters"))
async def set_filters(client, callback_query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Text", callback_data="filter_text"),
         InlineKeyboardButton("🖼️ Photo", callback_data="filter_photo")],
        [InlineKeyboardButton("🎥 Video", callback_data="filter_video"),
         InlineKeyboardButton("📄 Document", callback_data="filter_document")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
    ])
    await callback_query.message.edit_text("Select message types to forward:", reply_markup=keyboard)

# FILTER TOGGLE
@bot.on_callback_query(filters.regex("filter_(.*)"))
async def set_filter(client, callback_query):
    data = load_data()
    filter_type = callback_query.data.split("_")[1]
    current = data.get('filters', {}).get(filter_type, True)
    data['filters'][filter_type] = not current
    save_data(data)
    status = "✅ Enabled" if not current else "❌ Disabled"
    await callback_query.answer(f"{filter_type.capitalize()} {status}")

# HELP
@bot.on_callback_query(filters.regex("help"))
async def help_message(client, callback_query):
    await callback_query.message.edit_text(
        "ℹ️ **Bot Instructions:**\n"
        "- Add source and target channels.\n"
        "- Set what type of messages you want to forward.\n"
        "- Make sure the bot is **admin** in both channels.\n"
        "- Bot will copy messages (without forwarded tag).\n"
        "- If an error happens, the bot will send you the reason directly.\n"
        "- Enjoy your automation! 🚀"
    )

# MESSAGE FORWARDING
@bot.on_message(filters.chat(lambda _, __, message: message.chat.username in load_data()['sources']))
async def forward_message(client, message):
    data = load_data()
    filters_enabled = data.get('filters', {})
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
        for target in data['targets']:
            try:
                await message.copy(target)
            except Exception as e:
                try:
                    await client.send_message(ADMIN_CHAT_ID, f"❌ Error forwarding to {target}: {str(e)}")
                except:
                    pass

# Keep Alive (for UptimeRobot)
@app_web.route('/')
def home():
    return "Bot is Running!"

def run_web():
    app_web.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()

keep_alive()
bot.run()
