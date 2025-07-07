import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from yt_dlp import YoutubeDL

API_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

QUALITY_OPTIONS = [
    ("🎞 4K", "bestvideo[height<=2160]+bestaudio"),
    ("🎞 2K", "bestvideo[height<=1440]+bestaudio"),
    ("🎞 1080p", "bestvideo[height<=1080]+bestaudio"),
    ("🎞 720p", "bestvideo[height<=720]+bestaudio"),
    ("🎞 480p", "bestvideo[height<=480]+bestaudio"),
    ("🎞 360p", "bestvideo[height<=360]+bestaudio"),
    ("🎞 240p", "bestvideo[height<=240]+bestaudio"),
    ("🎞 144p", "bestvideo[height<=144]+bestaudio"),
    ("🎧 MP3 (только аудио)", "bestaudio")
]

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("👋 Привет! Отправь мне ссылку на видео с YouTube, TikTok, Instagram или другой платформы.")

@dp.message_handler(lambda message: message.text.startswith("http"))
async def handle_url(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    for text, fmt in QUALITY_OPTIONS:
        markup.add(types.InlineKeyboardButton(text, callback_data=f"{fmt}|{message.text}"))
    await message.answer("Выбери качество или формат:", reply_markup=markup)

@dp.callback_query_handler()
async def download_video(callback: types.CallbackQuery):
    await callback.answer("⏬ Скачиваю...")
    fmt, url = callback.data.split("|")
    user_id = callback.from_user.id

    ydl_opts = {
        'format': fmt,
        'outtmpl': f'{user_id}.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }] if 'audio' in fmt else []
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if 'audio' in fmt:
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'

        await bot.send_chat_action(user_id, types.ChatActions.UPLOAD_DOCUMENT)
        with open(file_path, 'rb') as f:
            await bot.send_document(user_id, f)

        os.remove(file_path)
    except Exception as e:
        await callback.message.answer(f"⚠️ Ошибка при скачивании: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
