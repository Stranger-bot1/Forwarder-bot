# combined_bot.py
import asyncio
import logging
import os
import re
import json
from pyrogram import Client, filters
from pyrogram.types import Message

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
    await message.reply(
        "\U0001F44B Welcome to the Combined Forwarder Bot!\n\n"
        "Commands:\n"
        "/add_target <chat_id>\n"
        "/remove_target <chat_id>\n"
        "/list_targets\n\n"
        "User Channel Forwarding:\n"
        "Send me: `source_id target_id`\n"
        "Send /stop to pause your forwarding."
    )


@app.on_message(filters.private & filters.command("stop"))
async def stop_command(client, message: Message):
    user_id = message.from_user.id
    if user_id in user_channels:
        user_channels[user_id]["active"] = False
        await message.reply("\U0001F6D8 Forwarding stopped for you.")
        await app.send_message(ADMIN_CHAT_ID, f"User {user_id} stopped forwarding.")
    else:
        await message.reply("\u26A0\uFE0F No active forwarding found.")


@app.on_message(filters.private & filters.command("add_target"))
async def add_target(client, message: Message):
    targets = load_targets()
    try:
        chat_id = int(message.text.split()[1])
        if chat_id not in targets:
            targets.append(chat_id)
            save_targets(targets)
            await message.reply(f"\u2705 Target {chat_id} added!")
        else:
            await message.reply("\u26A0\uFE0F Already added.")
    except:
        await message.reply("\u274C Provide a valid chat_id.\nExample: /add_target -1001234567890")


@app.on_message(filters.private & filters.command("remove_target"))
async def remove_target(client, message: Message):
    targets = load_targets()
    try:
        chat_id = int(message.text.split()[1])
        if chat_id in targets:
            targets.remove(chat_id)
            save_targets(targets)
            await message.reply(f"\u2705 Target {chat_id} removed!")
        else:
            await message.reply("\u26A0\uFE0F Target not found.")
    except:
        await message.reply("\u274C Provide a valid chat_id.\nExample: /remove_target -1001234567890")


@app.on_message(filters.private & filters.command("list_targets"))
async def list_targets(client, message: Message):
    targets = load_targets()
    if targets:
        await message.reply("\ud83d\udccd Targets:\n" + "\n".join([str(t) for t in targets]))
    else:
        await message.reply("\u2139\ufe0f No targets yet.")


# User channel linking
@app.on_message(filters.private & filters.text & ~filters.command(["start", "stop", "add_target", "remove_target", "list_targets"]))
async def get_channel_ids(client, message: Message):
    try:
        user_id = message.from_user.id
        ids = message.text.strip().split()

        if len(ids) != 2:
            await message.reply("\u2699\ufe0f Please send exactly two channel IDs separated by space: `source_id target_id`")
            return

        source_channel = int(ids[0])
        target_channel = int(ids[1])

        if user_id not in user_channels:
            user_channels[user_id] = {"channels": [], "active": True}

        user_channels[user_id]["channels"].append({"source": source_channel, "target": target_channel})
        user_channels[user_id]["active"] = True

        await message.reply(f"\u2705 Channel pair saved!\nSource: `{source_channel}`\nTarget: `{target_channel}`")
        await app.send_message(ADMIN_CHAT_ID, f"User {user_id} started forwarding from {source_channel} to {target_channel}.")

    except Exception as e:
        logger.error(f"Error while saving target channel: {e}")
        await message.reply("\u274C Error while processing your input.")


# Auto forwarding from channels (user-specific)
@app.on_message(filters.channel)
async def forward_channel_messages(client, message: Message):
    for user_id, user_data in user_channels.items():
        if user_data.get("active"):
            for channel_pair in user_data.get("channels", []):
                if message.chat.id == channel_pair["source"]:
                    try:
                        await asyncio.sleep(2)
                        await message.copy(chat_id=channel_pair["target"])

                        log_msg = f"\u2705 Forwarded message ID {message.id} from {channel_pair['source']} to {channel_pair['target']} (User {user_id})"
                        logger.info(log_msg)
                        await app.send_message(ADMIN_CHAT_ID, log_msg)

                    except Exception as e:
                        error_msg = f"\u274C Error forwarding message ID {message.id}: {e}"
                        logger.error(error_msg)
                        await app.send_message(ADMIN_CHAT_ID, error_msg)


# General Forwarding for All Chats
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
    logger.info("\ud83e\udd16 Combined Forwarder Bot is running...")
    app.run()
