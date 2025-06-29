from django.contrib import admin
from django.urls import path, include
from app.webhook import telegram_webhook

urlpatterns = [
    path('admin-panel/', admin.site.urls),
    path('api/', include('app.urls')),
    path('webhook/', telegram_webhook)
]
