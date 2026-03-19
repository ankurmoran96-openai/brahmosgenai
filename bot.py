import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, ADMIN_IDS
from database import init_db, add_user, is_user_allowed, allow_user
from llm_client import get_chat_response, get_models

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    logging.error("BOT_TOKEN is not set in environment or config.")
    exit(1)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

def get_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Check Available Models", callback_data="models")]
    ])
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    add_user(user_id, username)
    
    if user_id in ADMIN_IDS:
        allow_user(user_id)
        
    await message.answer("Welcome to *BrahMos GenAI Bot*! 🚀\nSend me a message to start chatting.", reply_markup=get_keyboard())

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("You are not authorized to use this command.")
        return
    await message.answer("Admin Panel:\nUse `/allow <user_id>` to approve a user.")

@dp.message(Command("allow"))
async def cmd_allow(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        target_id = int(message.text.split()[1])
        allow_user(target_id)
        await message.answer(f"User {target_id} has been allowed.")
    except (IndexError, ValueError):
        await message.answer("Usage: `/allow <user_id>`")

@dp.callback_query(F.data == "models")
async def cb_models(callback: types.CallbackQuery):
    models = await get_models()
    if models:
        model_list = "\n".join([f"- `{m}`" for m in models[:20]]) # Show first 20
        await callback.message.answer(f"*Available Models (showing 20):*\n{model_list}")
    else:
        await callback.message.answer("Could not fetch models.")
    await callback.answer()

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS and not is_user_allowed(user_id):
        await message.answer("You are not authorized to use this bot. Please ask an admin to approve you (give them your user ID).")
        return
        
    processing_msg = await message.answer("Thinking... ⏳")
    reply = await get_chat_response(user_id, message.text)
    
    # Send the response. Since ParseMode is Markdown, we need to handle formatting. 
    # If the text has unescaped characters, it might throw an error, but usually LLM output handles basic markdown well.
    try:
        await processing_msg.edit_text(reply)
    except Exception as e:
        # Fallback if markdown parsing fails
        await processing_msg.edit_text(reply, parse_mode=None)

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
