import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from yt_dlp import YoutubeDL

API_TOKEN = 'PASTE_YOUR_BOT_TOKEN_HERE'  # 👈 сюда вставь свой токен

# Установка ffmpeg (автоустановка на Railway)
os.system("apt update && apt install -y ffmpeg")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

user_links = {}

class DownloadState(StatesGroup):
    choosing_format = State()
    choosing_quality = State()

format_kb = ReplyKeyboardMarkup(resize_keyboard=True)
format_kb.add(KeyboardButton("🎬 Видео"), KeyboardButton("🎧 Музыка (mp3)"))

qualities = ["best", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
quality_kb = ReplyKeyboardMarkup(resize_keyboard=True)
for q in qualities:
    quality_kb.add(KeyboardButton(q))

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Пришли ссылку на видео (YouTube, TikTok, Instagram и др.).")

@dp.message_handler(lambda message: message.text and message.text.startswith("http"))
async def handle_link(message: types.Message, state: FSMContext):
    user_links[message.from_user.id] = message.text
    await message.answer("🔽 Что ты хочешь скачать?", reply_markup=format_kb)
    await DownloadState.choosing_format.set()

@dp.message_handler(state=DownloadState.choosing_format)
async def choose_format(message: types.Message, state: FSMContext):
    if message.text == "🎧 Музыка (mp3)":
        url = user_links.get(message.from_user.id)
        await message.answer("📥 Скачиваю музыку...")
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'music.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            with open("music.mp3", "rb") as audio:
                await message.answer_audio(audio)
            os.remove("music.mp3")
        except Exception as e:
            await message.answer(f"⚠️ Ошибка: {str(e)}")
        await state.finish()
    elif message.text == "🎬 Видео":
        await message.answer("Выбери качество:", reply_markup=quality_kb)
        await DownloadState.choosing_quality.set()
    else:
        await message.answer("Пожалуйста, выбери формат из меню.")

@dp.message_handler(state=DownloadState.choosing_quality)
async def choose_quality(message: types.Message, state: FSMContext):
    quality = message.text
    url = user_links.get(message.from_user.id)
    await message.answer(f"📥 Скачиваю видео ({quality})...")
    try:
        filename = "video.%(ext)s"
        ydl_opts = {
            'format': f'bestvideo[height={quality[:-1]}]+bestaudio/best' if quality != "best" else 'best',
            'outtmpl': filename,
            'merge_output_format': 'mp4',
            'quiet': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if not file_path.endswith(".mp4"):
                base = os.path.splitext(file_path)[0]
                file_path = base + ".mp4"
        with open(file_path, "rb") as video:
            await message.answer_video(video, caption=info.get("title", ""))
        os.remove(file_path)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {str(e)}")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
