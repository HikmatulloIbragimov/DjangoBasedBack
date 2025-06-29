from django.core.management.base import BaseCommand
from app.signals import yaml_generator

class Command(BaseCommand):
    help = 'Generate YAML files from database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--game',
            type=str,
            help='Generate YAML for specific game slug',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Generate all YAML files',
        )
    
    def handle(self, *args, **options):
        if options['game']:
            yaml_generator.generate_game_yaml(options['game'])
            self.stdout.write(
                self.style.SUCCESS(f'Successfully generated YAML for game: {options["game"]}')
            )
        elif options['all']:
            yaml_generator.generate_app_yaml()
            yaml_generator.generate_all_game_yamls()
            self.stdout.write(
                self.style.SUCCESS('Successfully generated all YAML files')
            )
        else:
            yaml_generator.generate_app_yaml()
            self.stdout.write(
                self.style.SUCCESS('Successfully generated app.yaml')
            )