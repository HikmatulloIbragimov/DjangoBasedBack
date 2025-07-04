import os
import yaml
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bek.settings')  # замените на свой модуль
django.setup()



from app.models import Game, Category, Server, Merchandise
from django.db.models.signals import post_save, post_delete
from app import signals

post_save.disconnect(signals.handle_game_change, sender=Game)
post_delete.disconnect(signals.handle_game_change, sender=Game)
post_save.disconnect(signals.handle_category_change, sender=Category)
post_delete.disconnect(signals.handle_category_change, sender=Category)
post_save.disconnect(signals.handle_server_change, sender=Server)
post_delete.disconnect(signals.handle_server_change, sender=Server)
post_save.disconnect(signals.handle_merchandise_change, sender=Merchandise)
post_delete.disconnect(signals.handle_merchandise_change, sender=Merchandise)

from app.models import Game, Category, Merchandise, Server

YAML_DIR = 'yaml_exports/game'  # Путь до папки с YAML

def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def import_game_from_yaml(file_path):
    data = load_yaml(file_path)
    game_data = data.get('game', {})

    game, _ = Game.objects.update_or_create(
        slug=game_data.get('slug'),
        defaults={
            'name': game_data.get('name', ''),
            'name_ru': game_data.get('name_ru', ''),
            'name_en': game_data.get('name_en', ''),
            'image_path': game_data.get('image_path', ''),
            'inputs': game_data.get('inputs', ''),
        }
    )

    # Сервера
    for srv in game_data.get('servers', []):
        Server.objects.update_or_create(
            slug=srv['slug'],
            defaults={
                'name': srv.get('name', ''),
                'name_ru': srv.get('name_ru', ''),
                'name_en': srv.get('name_en', ''),
            }
        )

    # Категории
    for cat in game_data.get('categories', []):
        Category.objects.update_or_create(
            slug=cat['slug'],
            defaults={
                'name': cat.get('name', ''),
                'name_ru': cat.get('name_ru', ''),
                'name_en': cat.get('name_en', ''),
                'description': cat.get('description', ''),
                'description_ru': cat.get('description_ru', ''),
                'description_en': cat.get('description_en', ''),
                'game': game.slug
            }
        )

    # Товары
    for merch in game_data.get('merchandise', []):
        prices = merch.get('prices', [{}])[0]
        tags = merch.get('tags', [])
        tag_string = ', '.join([t.get('name', '') for t in tags])
        Merchandise.objects.update_or_create(
            slug=merch['slug'],
            defaults={
                'name': merch.get('name', ''),
                'name_ru': merch.get('name_ru', ''),
                'name_en': merch.get('name_en', ''),
                'price': prices.get('price', 0),
                'currency': prices.get('currency', ''),
                'currency_ru': prices.get('currency_ru', ''),
                'currency_en': prices.get('currency_en', ''),
                'category': merch.get('category', ''),
                'server': merch.get('server', ''),
                'game': game.slug,
                'tags': tag_string,
                'enabled': True,
            }
        )

    print(f"[+] Imported game: {game.slug}")

def import_all_games():
    for filename in os.listdir(YAML_DIR):
        if filename.endswith('.yaml'):
            path = os.path.join(YAML_DIR, filename)
            import_game_from_yaml(path)

if __name__ == "__main__":
    import_all_games()
