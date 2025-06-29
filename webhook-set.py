import requests

def set_webhook(token, webhook_url):
    url = f"https://api.telegram.org/bot{token}/setWebhook"
    payload = {
        "url": webhook_url
    }
    response = requests.post(url, data=payload)
    return response.json()

set_webhook("8190740090:AAEDSCuLIRCFZbPAaEZwP0JztjkG7V9M4eA", "https://tezkor.kodi.uz/webhook/")