from django.contrib import admin
from .models import TelegramUser, Card, Game, Server, Category, Merchandise


admin.site.register([
    TelegramUser,
    Card,
    Game,
    Server,
    Category,
    Merchandise
])