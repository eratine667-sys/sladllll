import os
import asyncio
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Update

# --- НАСТРОЙКИ ---
API_TOKEN = os.environ.get('API_TOKEN')
# Твой реальный домен для вебхука
WEBHOOK_URL = "https://vercel.app"

app = Flask(__name__)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ЛОГИКА БОТА ---

@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🛠️ СНОС СЕССИЙ", callback_data="snos_start")
    kb.adjust(1)
    await message.answer("⚡ **CORE SYSTEM V4 ONLINE**\n\nВыбери модуль для работы:", 
                         reply_markup=kb.as_markup())

@dp.callback_query(F.data == "snos_start")
async def snos_step1(call: types.CallbackQuery):
    await call.message.answer("📞 **ШАГ 1:** Введите номер телефона жертвы (например, +7999...):")

@dp.message(F.text.startswith("+"))
async def snos_step2(message: types.Message):
    kb = InlineKeyboardBuilder()
    reasons = ["⚠️ Угрозы", "💸 Мошенничество", "🛡️ Обман", "🔞 Нарушение правил"]
    for r in reasons:
        kb.button(text=r, callback_data="wait_code_final")
    kb.adjust(1)
    kb.row(types.InlineKeyboardButton(text="📥 ЖДУ КОД", callback_data="wait_code_final"))
    
    await message.answer(f"🎯 Номер `{message.text}` принят.\nВыберите причину для инициации сброса:", 
                         reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "wait_code_final")
async def final_step(call: types.CallbackQuery):
    await call.message.answer("🚀 **ЗАПУСК МОДУЛЯ...**\n\n🛰️ Подключение к серверам...\n📍 IP инициатора: `используется`\n\n📥 **ОЖИДАЮ КОД ИЗ TELEGRAM...**", 
                              parse_mode="Markdown")

# --- САЙТ И АКТИВАЦИЯ ---

@app.route('/')
def home():
    return f'''
    <body style="background:#000;display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;color:#fff;font-family:sans-serif;">
        <h1 style="margin-bottom:20px;">⚡ CORE SYSTEM V4</h1>
        <a href="/activate" style="padding:15px 35px;background:#0088cc;color:#fff;text-decoration:none;border-radius:12px;font-weight:bold;box-shadow:0 0 25px #0088cc;">АКТИВИРОВАТЬ БОТА</a>
        <p style="margin-top:20px;color:#555;">Status: Online</p>
    </body>
    '''

@app.route('/activate')
def activate():
    try:
        # Принудительно ставим вебхук на нужный URL
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True))
        if success:
            return f"✅ СИСТЕМА ВООРУЖЕНА.<br>Webhook установлен на: {WEBHOOK_URL}"
        return "❌ ОШИБКА: Telegram не принял вебхук."
    except Exception as e:
        return f"❌ ОШИБКА: {str(e)}"

# Главный роут для приема сообщений (Webhook)
@app.route('/api/index', methods=['POST'])
def webhook():
    if request.method == 'POST':
        try:
            json_data = request.get_json(force=True)
            update = Update.de_json(json_data)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(dp.feed_update(bot, update))
            
            return "OK", 200
        except Exception as e:
            print(f"Error: {e}")
            return str(e), 500
    return "Method not allowed", 405

# Нужно для Vercel
app = app
