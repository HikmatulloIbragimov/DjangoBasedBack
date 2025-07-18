from django.urls import path
from .views import BalanceApi, UpdateUserApi, SendVerifyApi
from transaction.views import CreateTransactionApi
from app.views import get_app_yaml
from app.views import check_admin_id
from django.conf import settings
from app.views import get_game_yaml, get_app_yaml


urlpatterns = [
    path('balance/', BalanceApi.as_view()),
    path('update-user/', UpdateUserApi.as_view()),
    path('verify/', SendVerifyApi.as_view()),
    path('buy/', CreateTransactionApi.as_view()),
    path("cdn/config/app.yaml", get_app_yaml),
    path("cdn/config/game/<str:filename>.yaml", get_game_yaml),
    path("check-admin-id/", check_admin_id),
]
