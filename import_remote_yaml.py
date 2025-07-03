import os
import sys
import django
import requests
import yaml
from django.db import transaction

# Добавляем корень проекта в PYTHONPATH (если надо)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Устанавливаем переменную окружения с настройками Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'bek.settings'

print("DJANGO_SETTINGS_MODULE =", os.environ.get('DJANGO_SETTINGS_MODULE'))

# Инициализируем Django
django.setup()

from app.models import Category, Merchandise

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
            # Корректное декодирование с игнорированием ошибок
            text = res.content.decode('utf-8', errors='ignore')
            data = yaml.safe_load(text)
        except Exception as e:
            print(f"❌ Ошибка при загрузке {slug}: {e}")
            continue

        if not data:
            print(f"⚠️ Нет данных в YAML: {slug}")
            continue

        game_data = data.get("game")
        if not game_data:
            print(f"⚠️ Пропущено (нет ключа 'game'): {slug}")
            continue

        # Создаем/получаем категории
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

        # Обработка товаров (merchandise)
        merchandise = game_data.get("merchandise", [])
        for item in merchandise:
            # Предполагаем, что prices есть и первый элемент корректен
            price = item["prices"][0]["price"] if item.get("prices") else 0
            category = category_map.get(item.get("category"))
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

if __name__ == "__main__":
    import_remote_yamls()
