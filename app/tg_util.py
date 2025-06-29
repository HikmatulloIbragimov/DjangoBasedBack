import json
import requests
import time


def send_telegram_photo(bot_token, amount, user_id, image):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    reply_markup = json.dumps({
        "inline_keyboard": [
            [{"text": "Hammasi to'g'ri ✅", "callback_data": f"accept_{amount}_{user_id}"}]
        ]
    })

    files = {'photo': (image.name, image.read())}
    data = {
        "chat_id": "8146970004",
        "reply_markup": reply_markup,
        "caption": f"Summa: {amount} so'm"
    }

    try:
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram send error: {e}")


def send_transaction_info(bot_token, transaction):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    status_map = {
        "delivered": "Yetkazib berildi ! 100% ",
        "ontheway": "Yo‘lda, biroz kuting...",
        "failed": "Uzr, iloji bo'lmadi, operator bilan bog'laning!\nPastdan nima bo'lganini operatorga tushuntiring"
    }

    data = {
        "chat_id": transaction.user.user_id,
        "text": (
            f"📦 *Siz sotib oldingiz* #zakaz{transaction.id}\n"
            f"🛒 Mahsulot: {transaction.merchandise.name} | {transaction.quantity} dona\n"
            f"💵 Narx: {transaction.amount}\n"
            f"🕒 Qachon ?: {transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📥 Kalitlar:\n```json\n{json.dumps(transaction.inputs, indent=2, ensure_ascii=False)}\n```\n"
            f"✅ Status: {status_map.get(transaction.status, 'failed')}"
        ),
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram send error: {e}")


def send_transaction_done(bot_token, transaction, already=False):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    old_status = {
        "refunded": (
            "🛒 Buyurtma: #buyurtma{tid}\n"
            "🚫 Holat: Yetkazib berilmadi\n\n"
            "Afsuski, texnik sabablarga ko‘ra mahsulotni yetkazib bera olmadik.\n"
            "💸 Mablag‘ingiz avtomatik tarzda qaytarildi."
        ),
        "incorrect-detail": (
            "🛒 Buyurtma: #buyurtma{tid}\n"
            "❌ Holat: Noto‘g‘ri ma’lumot\n\n"
            "❗ Kiritilgan ma’lumotlar orqali akkauntingiz topilmadi.\n"
            "Iltimos, ID va server nomini tekshirib, qayta urinib ko‘ring.\n"
            "💸 To‘lovingiz qaytarildi."
        ),
    }

    new_status_map = {
        "delivered": (
            "🛒 Buyurtma: #buyurtma{tid}\n"
            "✅ Holat: Muvaffaqiyatli bajarildi\n\n"
            "🎉 Mahsulotingiz akkauntingizga to‘liq yetkazildi.\n"
            "Xaridingiz uchun tashakkur!"
        ),
        "ontheway": (
            "🛒 Buyurtma: #buyurtma{tid}\n"
            "⏳ Holat: Jarayonda\n\n"
            "🚚 Buyurtmangiz hozirda yetkazilmoqda.\n"
            "Iltimos, biroz kuting — tez orada mahsulot akkauntingizda bo‘ladi."
        ),
        "refunded": (
            "🛒 Buyurtma: #buyurtma{tid}\n"
            "⚠️ Holat: Rad etildi\n\n"
            "📛 Afsuski, siz tanlagan mahsulot siz o‘ynayotgan server uchun qo‘llab-quvvatlanmaydi.\n"
            "💸 To‘lovingiz bekor qilindi va qaytarildi."
        ),
        "incorrect-detail": (
            "🛒 Buyurtma: #buyurtma{tid}\n"
            "❌ Holat: Noto‘g‘ri ma’lumot\n\n"
            "❗ Kiritilgan ma’lumotlar orqali akkauntingiz topilmadi.\n"
            "Iltimos, ID va server nomini tekshirib, qayta urinib ko‘ring.\n"
            "💸 To‘lovingiz qaytarildi."
        ),
        "failed": (
            "🛒 Buyurtma: #buyurtma{tid}\n"
            "🔄 Holat: Yuborilmoqda\n\n"
            "📦 Mahsulotingizni yetkazish jarayoni boshlandi.\n"
            "⏱️ Iltimos, 10 soniyadan so‘ng holatni qayta tekshiring."
        ),
    }

    status_map = old_status if already else new_status_map

    text = status_map.get(transaction.status, "failed").format(tid=transaction.id)

    data = {
        "chat_id": transaction.user.user_id,
        "text": text,
        "parse_mode": "Markdown"
    }

    # Faqat aktiv statuslar uchun refresh tugmasi qo‘shiladi
    if transaction.status in ["ontheway", "failed"]:
        timestamp = int(time.time())
        data["reply_markup"] = json.dumps({
            "inline_keyboard": [
                [{"text": "🔄 Holatni yangilash", "callback_data": f"refresh_{transaction.id}_{timestamp}"}]
            ]
        })

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram send error: {e}")

