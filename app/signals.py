from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
import yaml
import os
from .models import Game, Server, Category, Merchandise, Card

class YAMLGenerator:
    def __init__(self):
        self.yaml_dir = getattr(settings, 'YAML_OUTPUT_DIR', 'yaml_exports')
        self.ensure_directory_exists()
    
    def ensure_directory_exists(self):
        """Create YAML output directory if it doesn't exist"""
        if not os.path.exists(self.yaml_dir):
            os.makedirs(self.yaml_dir)
    
    def generate_app_yaml(self):
        """Generate the main app.yaml file with games and cards"""
        try:
            # Get all games
            games_data = []
            for game in Game.objects.all():
                games_data.append({
                    'name': game.name,
                    'name_ru': game.name_ru,
                    'name_en': game.name_en,
                    'slug': game.slug,
                    'image_path': game.image_path
                })
            
            # Get all cards
            cards_data = []
            for card in Card.objects.all():
                cards_data.append({
                    'number': card.number,
                    'cardholder_name': card.cardholder_name
                })
            
            # Create the main structure
            app_data = {
                'games': games_data,
                'cards': cards_data
            }
            
            # Write to app.yaml
            app_yaml_path = os.path.join(self.yaml_dir, 'app.yaml')
            with open(app_yaml_path, 'w+', encoding='utf-8') as file:
                yaml.dump(app_data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            print(f"Generated app.yaml at {app_yaml_path}")
            
        except Exception as e:
            print(f"Error generating app.yaml: {e}")
    
    def generate_game_yaml(self, game_slug):
        """Generate individual game YAML file"""
        try:
            game = Game.objects.get(slug=game_slug)
            
            # Get servers for this game
            servers_data = []
            for server in game.servers.all():
                servers_data.append({
                    'name': server.name,
                    'name_ru': server.name_ru,
                    'name_en': server.name_en,
                    'slug': server.slug
                })
            
            # Get categories for this game
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
            
            # Get merchandise for this game
            merchandise_data = []
            for merch in Merchandise.objects.filter(game=game_slug, enabled=True):
                # Parse tags (assuming they're stored as comma-separated string)
                tags_list = []
                if merch.tags:
                    tag_names = merch.tags.split(',')
                    for tag_name in tag_names:
                        tags_list.append({'name': tag_name.strip()})
                
                # Parse prices (for now single price, but structure for multiple)
                prices_list = [{
                    'price': int(merch.price) if merch.price.isdigit() else merch.price,
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
                    'category': merch.category,
                    'tags': tags_list,
                    'server': merch.server,
                    'slug': merch.slug
                })
            
            # Create game structure
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
                yaml.dump(game_data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            print(f"Generated {game_slug}.yaml at {game_yaml_path}")
            
        except Game.DoesNotExist:
            print(f"Game with slug '{game_slug}' not found")
        except Exception as e:
            print(f"Error generating {game_slug}.yaml: {e}")
    
    def generate_all_game_yamls(self):
        """Generate YAML files for all games"""
        for game in Game.objects.all():
            self.generate_game_yaml(game.slug)

# Initialize the generator
yaml_generator = YAMLGenerator()

# Signal handlers
@receiver(post_save, sender=Game)
@receiver(post_delete, sender=Game)
def handle_game_change(sender, instance, **kwargs):
    """Handle Game model changes"""
    yaml_generator.generate_app_yaml()
    if hasattr(instance, 'slug'):
        yaml_generator.generate_game_yaml(instance.slug)

@receiver(post_save, sender=Card)
@receiver(post_delete, sender=Card)
def handle_card_change(sender, instance, **kwargs):
    """Handle Card model changes"""
    yaml_generator.generate_app_yaml()

@receiver(post_save, sender=Server)
@receiver(post_delete, sender=Server)
def handle_server_change(sender, instance, **kwargs):
    """Handle Server model changes"""
    # Regenerate all game YAMLs since servers are related to games
    yaml_generator.generate_all_game_yamls()

@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def handle_category_change(sender, instance, **kwargs):
    """Handle Category model changes"""
    # Regenerate all game YAMLs since categories are related to games
    yaml_generator.generate_all_game_yamls()

@receiver(post_save, sender=Merchandise)
@receiver(post_delete, sender=Merchandise)
def handle_merchandise_change(sender, instance, **kwargs):
    """Handle Merchandise model changes"""
    if hasattr(instance, 'game'):
        yaml_generator.generate_game_yaml(instance.game)
