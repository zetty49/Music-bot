import logging
import requests
import tempfile
import os
import tempfile
import pytube
import yt_dlp
import time
import ffmpeg 
import sqlite3 
import datetime

from dotenv import load_dotenv

import googleapiclient.discovery

from pydub import AudioSegment
from pytube.exceptions import RegexMatchError
from io import BytesIO
from aiogram.dispatcher import FSMContext
from aiogram.types import Update
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types.reply_keyboard import ReplyKeyboardRemove
from aiogram.types import InputFile
from aiogram.types import ChatActions
from pydub import AudioSegment
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Command, Text
from aiogram.types import ParseMode, InputFile, ChatType, CallbackQuery
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
import markups as nav

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")

storage = MemoryStorage()

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)

dp = Dispatcher(bot, storage=storage)

youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)

# ---Clear Directory func ---

def clear_music_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))




# --- DataBase ---

conn = sqlite3.connect('users.db')
cursor = conn.cursor()


cursor.execute('''CREATE TABLE IF NOT EXISTS users
              (id INTEGER PRIMARY KEY,
               username TEXT,
               first_name TEXT,
               last_name TEXT,
               date_added TEXT)''')

def add_user(user):
    date_added = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO users (id, username, first_name, last_name, date_added) VALUES (?, ?, ?, ?, ?)", 
                   (user.id, user.username, user.first_name, user.last_name, date_added))
    conn.commit()

def get_user_count():
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    return count

#class db:
# --- Search Function ---


async def search_music(query: str) -> list:
    request = youtube.search().list(
        part="id,snippet",
        q=query,
        type="video",
        videoDefinition="high",
        maxResults=10,
    )
    response = request.execute()
    videos = []
    for item in response["items"]:
        video_id = item["id"]["videoId"]
        video_title = item["snippet"]["title"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        videos.append({"title": video_title, "url": video_url})
    return videos

# Описываем состояние ожидания ввода названия песни
class SearchMusic(StatesGroup):
    waiting_for_music_query = State()

@dp.message_handler(Text(equals='🎵 Поиск по названию песни 🎵'))
async def search(message: types.Message):
    message_text = "Введите название песни:"
    await message.answer(message_text)

    # Переход в состояние ожидания названия песни
    await SearchMusic.waiting_for_music_query.set()

@dp.message_handler(state=SearchMusic.waiting_for_music_query)
async def search_music_query(message: types.Message, state: FSMContext):
    # Получаем название песни из сообщения пользователя
    query = message.text

    # Ищем песни по запросу
    results = await search_music(query)

    if results:
        # Формируем список кнопок с найденными песнями
        buttons = []
        for result in results:
            # Создаем кнопку с заголовком песни
            button = InlineKeyboardButton(text=result['title'], callback_data=result['url'])
            # Добавляем кнопку в список
            buttons.append([button])  # Оборачиваем кнопку в список

        # Создаем объект InlineKeyboardMarkup с кнопками
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)

        # Отправляем пользователю сообщение со списком найденных песен
        await bot.send_message(chat_id=message.from_user.id, text="Найденные песни:", reply_markup=markup)

    else:
        # Если песен не найдено, сообщаем об этом пользователю
        await bot.send_message(chat_id=message.from_user.id, text="По вашему запросу ничего не найдено.")

    # Сбрасываем состояние
    await state.finish()

#Загрузка аудиофайла

async def download_audio_from_youtube(url):
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]',
        'outtmpl': 'music\%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        info_dict = ydl.extract_info(url, download=False)
        audio_path = ydl.prepare_filename(info_dict)

        return audio_path
    

@dp.callback_query_handler(lambda callback_query: True)
async def process_callback_query(callback_query: types.CallbackQuery):
    # Получаем ссылку на видео из callback_data
    video_url = callback_query.data

    # Получаем аудио из видео на YouTube
    audio_file_path = await download_audio_from_youtube(video_url)

    # Отправляем аудиофайл
    with open(audio_file_path, 'rb') as audio_file:
        audio_bytes = audio_file.read()
        audio_bytesio = BytesIO(audio_bytes)
        audio_input_file = types.InputFile(audio_bytesio, filename=os.path.basename(audio_file_path))

    await bot.send_audio(callback_query.from_user.id, audio=audio_input_file)
    
    time.sleep(5)
    
    clear_music_folder('music')
           


# --- Приветствие ---

@dp.message_handler(commands= ['start'])
async def send_welcome(message: types.Message):
    user = message.from_user
    # проверяем, добавлен ли уже пользователь в базу данных
    cursor.execute("SELECT id FROM users WHERE id = ?", (user.id,))
    existing_user = cursor.fetchone()
    if existing_user is None:
        # если пользователь еще не добавлен, добавляем его в базу данных
        add_user(user)
    
    await bot.send_sticker(message.chat.id, sticker=r'CAACAgIAAxkBAAEH601j_GVbqimaDYzFWi6awjzH4Xnw0wACrQIAAjZ2IA6ZtuZmWWWEYC4E' )
    await bot.send_message(message.from_user.id, "Привет, {0.first_name}, я музыкальный  бот. \nПросто выбери что тебе нужно!".format(message.from_user), reply_markup = nav.mainMenu)

@dp.message_handler(commands=['sendall'])
async def sendall(message: types.Message):
    if message.from_user.id == 749034008:
        text = message.text[9:]
        #users = conn.get_u



@dp.message_handler()
async def bot_message(message: types.Message):
    
    if message.text == '🔙 Главное меню':
        await bot.send_message(message.from_user.id, '🔙 Главное меню', reply_markup=nav.mainMenu)
        
# --- search Music Menu ---


    elif message.text == '🎶 Поиск музыки 🎶':
        await bot.send_message(message.from_user.id, '🎶 Поиск музыки 🎶', reply_markup=nav.otherMenu)    
    
        



    elif message.text == '🤖 Мои функции 🤖':
        await bot.send_message(message.from_user.id, '🤖 Мои функции 🤖', reply_markup=nav.btnBack)
        await bot.send_message(message.from_user.id, 'Привет, я музыкальный бот \nС помощью кнопки 🎶 Поиск музыки 🎶 ты можешь найти песни которые тебе нужны \nТакже ты можешь найти все песни любого исполнител с помощью кнопки 🎤 Поиск по исполнителю 🎤, в меню 🎶 Поиск музыки 🎶\nИ если хочешь можешь посмотреть популярную музыку с помощью кнопки ❤️‍🔥 Популрная музыка ❤️‍🔥 в меню 🎶 Поиск музыки 🎶')

    elif message.text == '❤️‍🔥 Популрная музыка ❤️‍🔥':
        await bot.send_message(message.from_user.id, 'Эта функция сейчас в разработке')


def main():
    executor.start_polling(dp, skip_updates=True)

if __name__ == '__main__':
    main()
