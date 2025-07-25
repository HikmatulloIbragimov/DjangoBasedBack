import time, json, requests
import os
from django.conf import settings
def send_transaction_done(bot_token, transaction):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    status_map = {
        "delivered": "Yetkazib berildi ! 100% ",
        "ontheway": "Yo'lda, biroz kuting...",
        "failed": "Uzr, iloji bo'lmadi, operator bilan bog'laning!\nPastdan nima bo'lganini operatorga tushuntiring"
    }

    timestamp = int(time.time())

    reply_markup = json.dumps({
        "inline_keyboard": [
            [{"text": "🔄 Yangilash", "callback_data": f"refresh_{transaction.id}_{timestamp}"}]
        ]
    })

    data = {
        "chat_id": transaction.user.user_id,
        "text": (
            f"🛒 Mahsulot: #zakaz{transaction.id} yakunlandi \n"
            f"✅ Status: {status_map.get(transaction.status)}"
        ),
        "parse_mode": "Markdown",
        "reply_markup": reply_markup
    }

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram send error: {e}")

def get_admin_id():
    return int(os.getenv("TELEGRAM_ADMIN_ID"))


class transaction:
    def __init__(self, id, user, status):
        self.id = id
        self.user = user
        self.status = status


class User:
    def __init__(self, user_id):
        self.user_id = user_id




user = User(get_admin_id())
transaction = transaction("1", user, "delivered")


send_transaction_done(settings.TELEGRAM_BOT_TOKEN, transaction)