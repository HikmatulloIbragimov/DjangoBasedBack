from .models import Game, Server, Category, Merchandise, Card
from .signals import YAMLGenerator  # если YAMLGenerator находится в signals.py

def generate_all_yamls():
    yaml_generator = YAMLGenerator()
    yaml_generator.generate_app_yaml()
    yaml_generator.generate_all_game_yamls()
