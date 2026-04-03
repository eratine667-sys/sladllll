import os
import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройки
API_TOKEN = os.environ.get('API_TOKEN')
VERCEL_URL = f"https://{os.environ.get('VERCEL_URL')}" # Vercel сам подставит домен

app = Flask(__name__)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ЛОГИКА БОТА ---
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🛠️ СНОС СЕССИЙ", callback_data="snos")
    await message.answer("⚡ **CORE SYSTEM V4 ONLINE**", reply_markup=kb.as_markup())

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
    
    await message.answer(f"🎯 Номер `{message.text}` принят.\nВыбери причину для сброса:", 
                         reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "wait_code")
async def final_wait(call: types.CallbackQuery):
    await call.message.answer("🚀 **ЗАПУСК ПРОЦЕССА...**\nОжидаю код подтверждения...")

# --- САЙТ И АКТИВАЦИЯ ---
@app.route('/')
def home():
    return f'''
    <body style="background:#000;display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;color:#fff;font-family:sans-serif;">
        <h1 style="margin-bottom:20px;">⚡ CORE SYSTEM V4</h1>
        <a href="/activate" style="padding:15px 35px;background:#0088cc;color:#fff;text-decoration:none;border-radius:12px;font-weight:bold;box-shadow:0 0 25px #0088cc;">АКТИВИРОВАТЬ БОТА</a>
    </body>
    '''

@app.route('/activate')
def activate():
    # Устанавливаем вебхук на этот же файл
    webhook_url = f"{VERCEL_URL}/api/index"
    success = asyncio.run(bot.set_webhook(webhook_url))
    if success:
        return "✅ СИСТЕМА ВООРУЖЕНА. БОТ ПОДКЛЮЧЕН К ВЕБХУКУ."
    return "❌ ОШИБКА ПОДКЛЮЧЕНИЯ."

# Прием обновлений от Телеграм
@app.route('/api/index', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = types.Update.de_json(request.get_json(force=True))
        asyncio.run(dp.feed_update(bot, update))
        return "OK", 200
    return "!", 200

# Это точка входа для Vercel
app = app 
