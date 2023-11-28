from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

btnMain = KeyboardButton('🔙 Главное меню')

# --- Back button ---

btnBack = ReplyKeyboardMarkup(resize_keyboard = True,).add(btnMain)

# --- Main Menu ---

btnsearch = KeyboardButton('🎶 Поиск музыки 🎶')
btnhelp = KeyboardButton('🤖 Мои функции 🤖')
btnowner = KeyboardButton('🧔‍♂️ Мой владелец 🧔‍♂️')
btnreport = KeyboardButton('🆘 Сообщить об ошибке 🆘')
mainMenu = ReplyKeyboardMarkup(resize_keyboard = True).add(btnsearch, btnhelp,)


# --- Other Menu


btnsearchname = InlineKeyboardButton("🎵 Поиск по названию песни 🎵", callback_data='search_music')
btnsearchactor = KeyboardButton("🎤 Поиск по исполнителю 🎤")
bbtntopchart = KeyboardButton("❤️‍🔥 Популрная музыка ❤️‍🔥")
otherMenu = ReplyKeyboardMarkup(resize_keyboard =True).add(btnsearchname, bbtntopchart, btnMain)





    
