# --- ИСПРАВЛЕННЫЕ НАСТРОЙКИ ---
API_TOKEN = os.environ.get('API_TOKEN')
# Ставим вебхук ПРЯМО на api/index, где сидит обработчик
WEBHOOK_URL = "https://vercel.app"

# ... (весь твой код бота без изменений) ...

# --- ИСПРАВЛЕННЫЙ ВЕБХУК ---
@app.route('/api/index', methods=['POST', 'GET']) # Добавили GET для теста
def webhook_handler():
    if request.method == 'POST':
        try:
            json_data = request.get_json(force=True)
            update = Update.de_json(json_data)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(dp.feed_update(bot, update))
            
            return "OK", 200
        except Exception as e:
            return str(e), 500
    return "Ready to receive updates!", 200

# Для подстраховки: разрешим POST на главной, если Telegram туда забрел
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        return webhook_handler() # Перенаправляем на обработчик
    return f'''
    <body style="background:#000;display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;color:#fff;font-family:sans-serif;">
        <h1 style="margin-bottom:20px;">⚡ CORE SYSTEM V4</h1>
        <a href="/activate" style="padding:15px 35px;background:#0088cc;color:#fff;text-decoration:none;border-radius:12px;font-weight:bold;box-shadow:0 0 25px #0088cc;">АКТИВИРОВАТЬ БОТА</a>
        <p style="margin-top:20px;color:#555;">Status: Online</p>
    </body>
    '''
