from django.urls import path
from .views import BalanceApi, UpdateUserApi, SendVerifyApi
from transaction.views import CreateTransactionApi
from app.views import get_app_yaml
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path('balance/', BalanceApi.as_view()),
    path('update-user/', UpdateUserApi.as_view()),
    path('verify/', SendVerifyApi.as_view()),
    path('buy/', CreateTransactionApi.as_view()),
    path("cdn/config/app.yaml", get_app_yaml, name="get_app_yaml"),
] + static("/cdn/config/", document_root=os.path.join(settings.BASE_DIR, "static/config"))
