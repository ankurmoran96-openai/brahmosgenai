import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, URLInputFile
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import init_db, add_user
from llm_client import get_chat_response

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    logging.error("BOT_TOKEN is not set in environment or config.")
    exit(1)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

def get_start_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨‍💻 Developer", url="https://t.me/Ankxrrrr"),
            InlineKeyboardButton(text="📢 Channel", url="https://t.me/your_channel_here")
        ]
    ])
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    add_user(user_id, username)
    
    welcome_text = (
        "🚀 *Welcome to BrahMos GenAI!* 🚀\n\n"
        "I am a fully autonomous AI assistant. You don't need to use any special commands.\n\n"
        "Just talk to me naturally! Ask me questions, tell me to solve coding problems, or just say:\n"
        "`\"Create an image of a cyberpunk city\"`\n\n"
        "I will automatically figure out what tools to use and give you the best result.\n\n"
        "Let's chat! 👇"
    )
    
    await message.answer(welcome_text, reply_markup=get_start_keyboard())

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    
    # Optional typing action
    await bot.send_chat_action(chat_id=user_id, action="typing")
    processing_msg = await message.answer("Thinking... ⏳")
    
    response_data = await get_chat_response(user_id, message.text)
    
    text_reply = response_data.get("text", "Error getting response.")
    photo_url = response_data.get("photo_url")
    
    try:
        await processing_msg.delete()
    except Exception:
        pass

    try:
        if photo_url:
            # Send the image, with the text as caption (truncated if too long, max caption length is 1024)
            caption = text_reply if len(text_reply) <= 1024 else text_reply[:1020] + "..."
            # For simplicity, we just send photo and then the full text if it's too long
            await message.answer_photo(photo=URLInputFile(photo_url), caption=caption)
            if len(text_reply) > 1024:
                await message.answer(text_reply)
        else:
            await message.answer(text_reply)
    except Exception as e:
        # Fallback if markdown parsing fails
        if photo_url:
            await message.answer(f"Here is your image: {photo_url}\n\n{text_reply}", parse_mode=None)
        else:
            await message.answer(text_reply, parse_mode=None)

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
