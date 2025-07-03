import requests
import yaml
from django.conf import settings
from app.models import Category, Merchandise
from django.db import transaction
import os
import django

# Укажи путь к settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bek.settings')

# Инициализируй Django
django.setup()
# Список слугов (по URL можно понять структуру)
GAME_SLUGS = [
    "free-fire",
    "pubg",
    "fc-mobile",
    "leage-of-legends",
    "mobile-legends-global",
    "arena-of-valor-id",
    "hok",
    "genshin-impact",
    "blood-strike",
    "arena-breakout",
    "steam-gift-card-usd"
]

BASE_URL = "https://djangobasedback-production.up.railway.app/cdn/config/game/"

@transaction.atomic
def import_remote_yamls():
    for slug in GAME_SLUGS:
        url = f"{BASE_URL}{slug}.yaml"
        print(f"📥 Импортирую с URL: {url}")
        try:
            res = requests.get(url)
            res.raise_for_status()
            data = yaml.safe_load(res.text)
        except Exception as e:
            print(f"❌ Ошибка при загрузке {slug}: {e}")
            continue

        game_data = data.get("game")
        if not game_data:
            print(f"⚠️ Пропущено (не game): {slug}")
            continue

        # Категории
        categories = game_data.get("categories", [])
        category_map = {}
        for cat in categories:
            category, _ = Category.objects.get_or_create(
                slug=cat["slug"],
                defaults={
                    "name": cat["name"],
                    "name_ru": cat.get("name_ru", ""),
                    "name_en": cat.get("name_en", ""),
                    "description": cat.get("description", ""),
                    "description_ru": cat.get("description_ru", ""),
                    "description_en": cat.get("description_en", ""),
                }
            )
            category_map[cat["slug"]] = category

        # Товары
        merchandise = game_data.get("merchandise", [])
        for item in merchandise:
            price = item["prices"][0]["price"]
            category = category_map.get(item["category"])
            Merchandise.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "name_ru": item.get("name_ru", ""),
                    "name_en": item.get("name_en", ""),
                    "price": price,
                    "enabled": True,
                    "category": category,
                    "server": item.get("server", "")
                }
            )
    print("✅ Импорт с деплоя завершён.")
