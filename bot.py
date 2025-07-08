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
    return "✅ Auto Forwarder Bot is Live."


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
        data[user_id] = {
            "sources": [],
            "targets": [],
            "filters": {"text": True, "photo": True, "video": True, "document": True},
            "is_active": True
        }
        save_data(data)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 My Sources", callback_data=f"sources_{user_id}")],
        [InlineKeyboardButton("🎯 My Targets", callback_data=f"targets_{user_id}")],
        [InlineKeyboardButton("⚙️ My Filters", callback_data=f"filters_{user_id}")],
        [InlineKeyboardButton("▶️ Start Forwarding", callback_data=f"start_{user_id}"),
         InlineKeyboardButton("⏹️ Stop Forwarding", callback_data=f"stop_{user_id}")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ])
    await message.reply("👋 Welcome to your Auto Forwarder Bot Dashboard. Use the buttons below to control the bot:", reply_markup=keyboard)


@bot.on_message(filters.command("addsource"))
async def add_source(client, message):
    user_id = str(message.from_user.id)
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ Usage: /addsource <@channel_username>")
        return

    channel = args[1]
    data = load_data()
    if channel not in data.get(user_id, {}).get("sources", []):
        data[user_id]["sources"].append(channel)
        save_data(data)
        await message.reply(f"✅ Source channel {channel} added successfully.")
    else:
        await message.reply("⚠️ This channel is already added as source.")


@bot.on_message(filters.command("addtarget"))
async def add_target(client, message):
    user_id = str(message.from_user.id)
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ Usage: /addtarget <@channel_username>")
        return

    channel = args[1]
    data = load_data()
    if channel not in data.get(user_id, {}).get("targets", []):
        data[user_id]["targets"].append(channel)
        save_data(data)
        await message.reply(f"✅ Target channel {channel} added successfully.")
    else:
        await message.reply("⚠️ This channel is already added as target.")


@bot.on_message(filters.command("removesource"))
async def remove_source(client, message):
    user_id = str(message.from_user.id)
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ Usage: /removesource <@channel_username>")
        return

    channel = args[1]
    data = load_data()
    if channel in data.get(user_id, {}).get("sources", []):
        data[user_id]["sources"].remove(channel)
        save_data(data)
        await message.reply(f"🗑️ Removed source: {channel}")
    else:
        await message.reply("⚠️ That channel is not in your source list.")


@bot.on_message(filters.command("removetarget"))
async def remove_target(client, message):
    user_id = str(message.from_user.id)
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❗ Usage: /removetarget <@channel_username>")
        return

    channel = args[1]
    data = load_data()
    if channel in data.get(user_id, {}).get("targets", []):
        data[user_id]["targets"].remove(channel)
        save_data(data)
        await message.reply(f"🗑️ Removed target: {channel}")
    else:
        await message.reply("⚠️ That channel is not in your target list.")


@bot.on_message(filters.command("filters"))
async def toggle_filters(client, message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data:
        await message.reply("⚠️ Please start the bot using /start first.")
        return

    filters_text = "\n".join([f"{k.capitalize()}: {'✅' if v else '❌'}" for k, v in data[user_id]["filters"].items()])
    reply_text = f"⚙️ Current Filters:\n{filters_text}\n\nSend one of these to toggle: text, photo, video, document"
    await message.reply(reply_text)


@bot.on_message(filters.text & filters.private)
async def handle_filter_toggle(client, message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data:
        return

    toggle_key = message.text.strip().lower()
    if toggle_key in data[user_id]["filters"]:
        data[user_id]["filters"][toggle_key] = not data[user_id]["filters"][toggle_key]
        save_data(data)
        status = "✅ Enabled" if data[user_id]["filters"][toggle_key] else "❌ Disabled"
        await message.reply(f"{toggle_key.capitalize()} filter is now {status}.")


@bot.on_message(filters.command("checksource"))
async def check_source(client, message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id not in data or not data[user_id]['sources']:
        await message.reply("⚠️ No source channels added. Use /addsource <channel_username>")
        return

    reply_text = "🔍 Checking your source channels:\n"
    for source in data[user_id]['sources']:
        try:
            await client.get_chat_member(source, 'me')
            reply_text += f"✅ Bot is in source: {source}\n"
        except:
            reply_text += f"❌ Bot is NOT in source: {source} — It may be public, so messages might still work.\n"
    await message.reply(reply_text)


@bot.on_message(filters.command("startforwarding"))
async def start_forwarding(client, message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id in data:
        data[user_id]['is_active'] = True
        save_data(data)
        await message.reply("✅ Auto Forwarding Activated.")
    else:
        await message.reply("⚠️ Set up your sources and targets first.")


@bot.on_message(filters.command("stopforwarding"))
async def stop_forwarding(client, message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id in data:
        data[user_id]['is_active'] = False
        save_data(data)
        await message.reply("⛔ Auto Forwarding Stopped.")
    else:
        await message.reply("⚠️ Set up your sources and targets first.")


@bot.on_callback_query()
async def handle_callbacks(client, callback_query: CallbackQuery):
    user_id = str(callback_query.from_user.id)
    data = load_data()

    if callback_query.data.startswith("start_"):
        data[user_id]['is_active'] = True
        save_data(data)
        await callback_query.answer("✅ Forwarding started.", show_alert=True)

    elif callback_query.data.startswith("stop_"):
        data[user_id]['is_active'] = False
        save_data(data)
        await callback_query.answer("⛔ Forwarding stopped.", show_alert=True)

    elif callback_query.data.startswith("sources_"):
        await callback_query.answer("ℹ️ Add source using /addsource <@channel_username>", show_alert=True)

    elif callback_query.data.startswith("targets_"):
        await callback_query.answer("ℹ️ Add target using /addtarget <@channel_username>", show_alert=True)

    elif callback_query.data.startswith("filters_"):
        await callback_query.answer("ℹ️ Use /filters to toggle forwarding filters.", show_alert=True)

    elif callback_query.data == "help":
        await callback_query.answer(
            "📘 Help Menu:\n"
            "1. /addsource <channel> - Add source channel.\n"
            "2. /addtarget <channel> - Add target channel.\n"
            "3. /filters - Customize what to forward.\n"
            "4. /startforwarding /stopforwarding - Control auto-forwarding.",
            show_alert=True
        )


@bot.on_message(filters.group | filters.channel)
async def forward_message(client, message):
    data = load_data()
    processed_users = set()

    for user_id, user_data in data.items():
        if not user_data.get("is_active", True):
            continue

        if message.chat.username in user_data["sources"] and user_id not in processed_users:
            filters_enabled = user_data.get("filters", {})
            allowed = (
                (message.text and filters_enabled.get("text", True)) or
                (message.photo and filters_enabled.get("photo", True)) or
                (message.video and filters_enabled.get("video", True)) or
                (message.document and filters_enabled.get("document", True))
            )

            if allowed:
                for target in user_data["targets"]:
                    try:
                        await message.copy(target)
                    except Exception as e:
                        try:
                            await client.send_message(int(user_id), f"❌ Error sending to {target}: {e}")
                        except:
                            pass
                processed_users.add(user_id)


keep_alive()
bot.run()
