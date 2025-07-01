# telegram_forwarder_bot.py
import asyncio
import logging
import os
import re
import json
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot credentials (provided)
API_ID = 24344133
API_HASH = "edbe7000baef13fa5a6c45c8edc4be66"
BOT_TOKEN = "7790100613:AAFrRb6Amtpu5XAos0iuqb85Y05bEXsu_sg"
ADMIN_CHAT_ID = 123456789  # Replace with your Telegram User ID

# Storage files
TARGETS_FILE = "targets.json"

# In-memory storage for user-specific forwarding
user_channels = {}

# Initialize Bot
app = Client("file_storing_gpt_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# KeepAlive Setup (for Render & UptimeRobot)
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "🤖 Bot is Alive!"

def run():
    flask_app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()


def load_targets():
    try:
        with open(TARGETS_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_targets(targets):
    with open(TARGETS_FILE, "w") as f:
        json.dump(targets, f)


def clean_text(text):
    if not text:
        return ""
    cleaned_text = re.sub(r'@\w+', '', text)
    return cleaned_text.strip()


# General Commands
@app.on_message(filters.private & filters.command("start"))
async def start_command(client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Add Target", callback_data="add_target"), InlineKeyboardButton("Remove Target", callback_data="remove_target")],
        [InlineKeyboardButton("List Targets", callback_data="list_targets")],
        [InlineKeyboardButton("Help", callback_data="help")]
    ])
    await message.reply(
        "👋 **Welcome to File Sender Bot!**\n\n"
        "Here’s what I can do for you:\n"
        "✅ Add Global Targets (/add_target <chat_id>)\n"
        "✅ Remove Targets (/remove_target <chat_id>)\n"
        "✅ List Targets (/list_targets)\n"
        "✅ Send me channel IDs like: source_id target_id\n"
        "✅ Stop forwarding: /stop\n\n"
        "💡 **Note:** Use only Telegram Channel IDs starting with `-100`.",
        reply_markup=keyboard
    )


@app.on_callback_query()
async def handle_callback(client, callback_query):
    data = callback_query.data
    if data == "add_target":
        await callback_query.message.reply("Use this command to add a target: /add_target -100XXXXXXXXXX")
    elif data == "remove_target":
        await callback_query.message.reply("Use this command to remove a target: /remove_target -100XXXXXXXXXX")
    elif data == "list_targets":
        await callback_query.message.reply("Use this command to list targets: /list_targets")
    elif data == "help":
        await callback_query.message.reply(
            "🔗 **Help Menu:**\n"
            "- Add Target: /add_target -100XXXXXXXXXX\n"
            "- Remove Target: /remove_target -100XXXXXXXXXX\n"
            "- List Targets: /list_targets\n"
            "- Stop Forwarding: /stop\n\n"
            "Send me source and target channel IDs separated by space to start forwarding."
        )


@app.on_message(filters.private & filters.command("stop"))
async def stop_command(client, message: Message):
    user_id = message.from_user.id
    if user_id in user_channels:
        user_channels[user_id]["active"] = False
        await message.reply("🚘 Forwarding stopped for you.")
        await app.send_message(ADMIN_CHAT_ID, f"User {user_id} stopped forwarding.")
    else:
        await message.reply("⚠️ You don’t have any active forwarding.")


@app.on_message(filters.private & filters.command("add_target"))
async def add_target(client, message: Message):
    targets = load_targets()
    try:
        chat_id = int(message.text.split()[1])
        if str(chat_id).startswith("-100"):
            if chat_id not in targets:
                targets.append(chat_id)
                save_targets(targets)
                await message.reply(f"✅ Target {chat_id} added successfully!")
            else:
                await message.reply("⚠️ This target is already added.")
        else:
            await message.reply("⚠️ Please send a valid Telegram channel ID starting with -100.")
    except:
        await message.reply("❌ Please send a valid format. Example: /add_target -1001234567890")


@app.on_message(filters.private & filters.command("remove_target"))
async def remove_target(client, message: Message):
    targets = load_targets()
    try:
        chat_id = int(message.text.split()[1])
        if chat_id in targets:
            targets.remove(chat_id)
            save_targets(targets)
            await message.reply(f"✅ Target {chat_id} removed successfully!")
        else:
            await message.reply("⚠️ This target was not found in your list.")
    except:
        await message.reply("❌ Please send a valid format. Example: /remove_target -1001234567890")


@app.on_message(filters.private & filters.command("list_targets"))
async def list_targets(client, message: Message):
    targets = load_targets()
    if targets:
        await message.reply("📍 **Current Targets:**\n" + "\n".join([str(t) for t in targets]))
    else:
        await message.reply("ℹ️ No global targets added yet.")


# User channel linking with friendly errors
@app.on_message(filters.private & filters.text & ~filters.command(["start", "stop", "add_target", "remove_target", "list_targets"]))
async def get_channel_ids(client, message: Message):
    try:
        user_id = message.from_user.id
        ids = message.text.strip().split()

        if len(ids) != 2:
            await message.reply("⚙️ Please send exactly two **Telegram Channel IDs** separated by space.\nExample: `-1001234567890 -1009876543210`")
            return

        source_channel = ids[0]
        target_channel = ids[1]

        if not (source_channel.startswith("-100") and target_channel.startswith("-100")):
            await message.reply("⚠️ Please send valid Telegram channel IDs starting with `-100`.\nExample: `-1001234567890 -1009876543210`")
            return

        source_channel = int(source_channel)
        target_channel = int(target_channel)

        if user_id not in user_channels:
            user_channels[user_id] = {"channels": [], "active": True}

        user_channels[user_id]["channels"].append({"source": source_channel, "target": target_channel})
        user_channels[user_id]["active"] = True

        await message.reply(f"✅ Channel pair saved successfully!\n\nSource: `{source_channel}`\nTarget: `{target_channel}`")
        await app.send_message(ADMIN_CHAT_ID, f"User {user_id} started forwarding from {source_channel} to {target_channel}.")

    except Exception as e:
        logger.error(f"Error while saving target channel: {e}")
        await message.reply(f"❌ Error while processing your input. Reason: {e}")


@app.on_message(filters.channel)
async def forward_channel_messages(client, message: Message):
    for user_id, user_data in user_channels.items():
        if user_data.get("active"):
            for channel_pair in user_data.get("channels", []):
                if message.chat.id == channel_pair["source"]:
                    try:
                        await asyncio.sleep(2)
                        await message.copy(chat_id=channel_pair["target"])

                        log_msg = f"✅ Forwarded message ID {message.id} from {channel_pair['source']} to {channel_pair['target']} (User {user_id})"
                        logger.info(log_msg)
                        await app.send_message(ADMIN_CHAT_ID, log_msg)

                    except Exception as e:
                        error_msg = f"❌ Error forwarding message ID {message.id}: {e}"
                        logger.error(error_msg)
                        await app.send_message(ADMIN_CHAT_ID, error_msg)
                        await app.send_message(user_id, f"❌ Failed to forward your message from {channel_pair['source']} to {channel_pair['target']}. Reason: {e}")


@app.on_message(filters.group | filters.channel | filters.private)
async def forward_general_messages(client, message: Message):
    if message.text or message.caption or message.photo or message.video or message.audio or message.document:
        targets = load_targets()
        if not targets:
            return

        try:
            if message.text:
                cleaned_text = clean_text(message.text)
                for target in targets:
                    await app.send_message(chat_id=target, text=cleaned_text)

            elif message.caption:
                cleaned_caption = clean_text(message.caption)
                if message.photo:
                    for target in targets:
                        await app.send_photo(chat_id=target, photo=message.photo.file_id, caption=cleaned_caption)
                elif message.video:
                    for target in targets:
                        await app.send_video(chat_id=target, video=message.video.file_id, caption=cleaned_caption)
                elif message.document:
                    for target in targets:
                        await app.send_document(chat_id=target, document=message.document.file_id, caption=cleaned_caption)
                elif message.audio:
                    for target in targets:
                        await app.send_audio(chat_id=target, audio=message.audio.file_id, caption=cleaned_caption)

            elif message.photo:
                for target in targets:
                    await app.send_photo(chat_id=target, photo=message.photo.file_id)

            elif message.video:
                for target in targets:
                    await app.send_video(chat_id=target, video=message.video.file_id)

            elif message.document:
                for target in targets:
                    await app.send_document(chat_id=target, document=message.document.file_id)

            elif message.audio:
                for target in targets:
                    await app.send_audio(chat_id=target, audio=message.audio.file_id)

        except Exception as e:
            logger.error(f"Error forwarding: {e}")


if __name__ == "__main__":
    keep_alive()
    logger.info("🤖 Telegram Forwarder Bot is running...")
    app.run()
