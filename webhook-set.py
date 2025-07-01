import requests
from django.conf import settings
def set_webhook(token, webhook_url):
    url = f"https://api.telegram.org/bot{token}/setWebhook"
    payload = {
        "url": webhook_url
    }
    response = requests.post(url, data=payload)
    return response.json()

set_webhook(settings.TELEGRAM_BOT_TOKEN, settings.WEBHOOK_URL)