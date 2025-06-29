import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
from .models import TelegramUser
from django.conf import settings
from transaction.tasks import refresh_status
import time


@csrf_exempt
def telegram_webhook(request):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    admin_id = settings.TELEGRAM_ADMIN_ID

    data = json.loads(request.body.decode("utf-8"))

    message = data.get("message")
    callback = data.get("callback_query")

    # print(message)

    chat_id = (message["chat"]["id"] if message else callback["message"]["chat"]["id"])
    
    if message:
        if "reply_to_message" in message:
            replied_msg = message["reply_to_message"]
            
            if replied_msg.get("caption", "").startswith("Summa") and replied_msg.get("caption", "").endswith("so'm"):
                keyboard = replied_msg.get("reply_markup", {}).get("inline_keyboard", [])

                if len(keyboard) == 1 and keyboard[0]:
                    callback_data = keyboard[0][0]["callback_data"]
                    parts = callback_data.split("_")
                    if len(parts) == 3:
                        user_id = parts[2]

                photos = replied_msg.get("photo", [])
                if photos:
                    image = photos[-1]["file_id"]
                
                if message["text"].isnumeric():
                    amount = int(message["text"])

                send_telegram_photo(bot_token, admin_id, amount, user_id, image)

        text = message.get("text", "")

        if text == "/start":
            send_inline_image_with_buttons(bot_token, chat_id)

    elif callback:
        cb_data = callback["data"]
        callback_id = callback["id"]

        if cb_data == "instructions":
            send_info(bot_token, chat_id)

        if cb_data == "contact":
            send_admin(bot_token, chat_id)

        if cb_data.startswith("accept"):
            try:
                _, amount, user_id = cb_data.split("_")

                TelegramUser.objects.filter(
                    user_id=user_id
                ).update(
                    balance=F('balance') + int(amount)
                )

            except Exception as e:
                print(e)

            delete_message(bot_token, chat_id,
                           callback["message"]["message_id"])
        
        
        if cb_data.startswith("refresh"):
            _, transaction_id, timestamp = cb_data.split("_")
            try:
                timestamp = int(timestamp)
                now = int(time.time())

                if now - timestamp >= 10:
                    refresh_status.delay(transaction_id)
                else:
                    answer_callback_query(bot_token, callback_id, f"{10 - (now - timestamp)} soniyada qayta bosishingiz mumkin")
            except Exception as e:
                print("Refresh error:", e)

        answer_callback_query(bot_token, callback_id)

    return JsonResponse({"ok": True})


def send_telegram_photo(bot_token, admin_id, amount, user_id, image):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    reply_markup = json.dumps({
        "inline_keyboard": [
            [{"text": "Hammasi to'g'ri ✅", "callback_data": f"accept_{amount}_{user_id}"}]
        ]
    })

    
    data = {
        "chat_id": admin_id,
        "reply_markup": reply_markup,
        "caption": f"Summa: {amount} so'm",
        "photo": image
    }

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram send error: {e}")

def answer_callback_query(token, callback_query_id, text=None, show_alert=False):
    url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
    payload = {
        "callback_query_id": callback_query_id,
        "text": text,
        "show_alert": show_alert
    }
    requests.post(url, json=payload)

def delete_message(token, chat_id, message_id):
    url = f"https://api.telegram.org/bot{token}/deleteMessage"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id
    }
    requests.post(url, json=payload)

def send_admin(token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "parse_mode": "Markdown",
        "text": (
            "*🚀 Tez Donatchi Bot*\n"
            "[🔗 @TezDonatchiBot](https://t.me/TezDonatchiBot)\n"
            "[👨‍💻 Admin bilan bog‘lanish](https://t.me/TezDonatchiAdmin)\n\n"
            "_Donat qilish hech qachon bunchalik tez bo‘lmagan!_ 💸"
        )
    }
    requests.post(url, json=payload)

def send_info(token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "parse_mode": "Markdown",
        "text": (
            "🎮 *Kerakli o‘yin valyutalarini* yoki *sovg‘alarni* tanlang!\n\n"
            "⬆️ *Yuqoridagi \"Start bot\" tugmasini* bosing\n"
            "💵 O‘zbek so‘mida *oson va tez* xarid qiling!"
        )
    }
    requests.post(url, json=payload)



def send_inline_image_with_buttons(token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": "https://tezkor-donat-front.vercel.app/logo.png",
        "reply_markup": json.dumps({
            "inline_keyboard": [
                [{
                    "text": "🚀 Start bot",
                    "web_app": {"url": "https://tezkor-donat-front.vercel.app/"}
                }],
                [
                    {"text": "📞 Admin", "callback_data": "contact"},
                    {"text": "📖 Ma'lumotlar", "callback_data": "instructions"}
                ]
            ]
        })
    }
    response = requests.post(url, data=payload)
    print(response.text)
