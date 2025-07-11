from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
import yaml
import os
import threading
from .models import Game, Server, Category, Merchandise, Card

# 🔒 Флаг для временного отключения сигналов
block_yaml_signals = threading.local()
block_yaml_signals.disabled = False


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


class YAMLGenerator:
    def __init__(self):
        self.yaml_dir = getattr(settings, 'YAML_OUTPUT_DIR', 'yaml_exports')
        self.ensure_directory_exists()
    
    def ensure_directory_exists(self):
        if not os.path.exists(self.yaml_dir):
            os.makedirs(self.yaml_dir)
    
    def generate_app_yaml(self):
        try:
            games_data = []
            for game in Game.objects.all():
                games_data.append({
                    'name': game.name,
                    'name_ru': game.name_ru,
                    'name_en': game.name_en,
                    'slug': game.slug,
                    'image_path': game.image_path
                })

            cards_data = []
            for card in Card.objects.all():
                cards_data.append({
                    'number': card.number,
                    'cardholder_name': card.cardholder_name
                })

            app_data = {
                'games': games_data,
                'cards': cards_data
            }

            app_yaml_path = os.path.join(self.yaml_dir, 'app.yaml')
            with open(app_yaml_path, 'w', encoding='utf-8') as file:
                yaml.dump(app_data, file, Dumper=NoAliasDumper, allow_unicode=True, default_flow_style=False, sort_keys=False)

            print(f"Generated app.yaml at {app_yaml_path}")
        except Exception as e:
            print(f"Error generating app.yaml: {e}")
    
    def generate_game_yaml(self, game_slug):
        print("[DEBUG] Generating merch for:", game_slug)
        print("[DEBUG] Found:", Merchandise.objects.filter(game=game_slug, enabled=True).count())
        try:
            game = Game.objects.get(slug=game_slug)

            servers_data = []
            for server in game.servers.all():
                servers_data.append({
                    'name': server.name,
                    'name_ru': server.name_ru,
                    'name_en': server.name_en,
                    'slug': server.slug
                })

            categories_data = []
            for category in game.categories.all():
                categories_data.append({
                    'name': category.name,
                    'name_ru': category.name_ru,
                    'name_en': category.name_en,
                    'description': category.description,
                    'description_ru': category.description_ru,
                    'description_en': category.description_en,
                    'slug': category.slug
                })

            merchandise_data = []
            for merch in Merchandise.objects.filter(game=game_slug, enabled=True):
                tags_list = []
                if merch.tags:
                    tag_names = merch.tags.split(',')
                    tags_list = [{'name': tag.strip()} for tag in tag_names]

                prices_list = [{
                    'price': int(merch.price) if str(merch.price).isdigit() else merch.price,
                    'currency': merch.currency,
                    'currency_ru': merch.currency_ru,
                    'currency_en': merch.currency_en
                }]

                merchandise_data.append({
                    'id': merch.id,
                    'name': merch.name,
                    'name_ru': merch.name_ru,
                    'name_en': merch.name_en,
                    'prices': prices_list,
                    'category': merch.category or '',
                    'tags': tags_list,
                    'server': merch.server or '',
                    'slug': merch.slug
                })

            game_data = {
                'game': {
                    'name': game.name,
                    'name_ru': game.name_ru,
                    'name_en': game.name_en,
                    'slug': game.slug,
                    'image_path': game.image_path,
                    'servers': servers_data,
                    'inputs': game.inputs,
                    'categories': categories_data,
                    'merchandise': merchandise_data
                }
            }

            os.makedirs(os.path.join(self.yaml_dir, 'game'), exist_ok=True)
            game_yaml_path = os.path.join(self.yaml_dir, f'game/{game_slug}.yaml')
            with open(game_yaml_path, 'w+', encoding='utf-8') as file:
                yaml.dump(game_data, file, Dumper=NoAliasDumper, allow_unicode=True, default_flow_style=False, sort_keys=False)

            print(f"Generated {game_slug}.yaml at {game_yaml_path}")
        except Game.DoesNotExist:
            print(f"Game with slug '{game_slug}' not found")
        except Exception as e:
            print(f"Error generating {game_slug}.yaml: {e}")
    
    def generate_all_game_yamls(self):
        for game in Game.objects.all():
            self.generate_game_yaml(game.slug)


# Инициализация генератора
yaml_generator = YAMLGenerator()


# ========== СИГНАЛЫ ==========
def skip_if_disabled(func):
    def wrapper(sender, instance, **kwargs):
        if getattr(block_yaml_signals, 'disabled', False):
            return
        return func(sender, instance, **kwargs)
    return wrapper


@receiver(post_save, sender=Game)
@receiver(post_delete, sender=Game)
@skip_if_disabled
def handle_game_change(sender, instance, **kwargs):
    yaml_generator.generate_app_yaml()
    if hasattr(instance, 'slug'):
        yaml_generator.generate_game_yaml(instance.slug)


@receiver(post_save, sender=Card)
@receiver(post_delete, sender=Card)
@skip_if_disabled
def handle_card_change(sender, instance, **kwargs):
    yaml_generator.generate_app_yaml()


@receiver(post_save, sender=Server)
@receiver(post_delete, sender=Server)
@skip_if_disabled
def handle_server_change(sender, instance, **kwargs):
    yaml_generator.generate_all_game_yamls()


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
@skip_if_disabled
def handle_category_change(sender, instance, **kwargs):
    yaml_generator.generate_all_game_yamls()


@receiver(post_save, sender=Merchandise)
@receiver(post_delete, sender=Merchandise)
@skip_if_disabled
def handle_merchandise_change(sender, instance, **kwargs):
    if hasattr(instance, 'game'):
        yaml_generator.generate_game_yaml(instance.game.slug)
