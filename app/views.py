from django.views import View
from django.http import JsonResponse
from .models import TelegramUser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import threading
import json
import base64
import os
from django.conf import settings
from .tg_util import send_telegram_photo
from django.http import FileResponse, Http404, HttpResponse
def get_app_yaml(request):
    yaml_path = os.path.join(settings.YAML_OUTPUT_DIR, 'app.yaml')
    if not os.path.exists(yaml_path):
        raise Http404("app.yaml не найден")
    
    with open(yaml_path, 'rb') as f:
        content = f.read()

    response = HttpResponse(content, content_type='text/yaml; charset=utf-8')
    response['Content-Disposition'] = 'inline; filename="app.yaml"'
    return response

def get_game_yaml(request, filename):
    yaml_path = os.path.join(settings.YAML_OUTPUT_DIR, 'game', f'{filename}.yaml')
    print(f"Serving {filename}.yaml from: {yaml_path}, exists: {os.path.exists(yaml_path)}")
    if not os.path.exists(yaml_path):
        raise Http404("YAML файл не найден")
    return FileResponse(open(yaml_path, 'rb'), content_type="text/yaml")

def get_user(request):
    encoded_user = request.headers.get("X-User-ID")
    user_data = None

    if not encoded_user:
        return JsonResponse({"error": "Missing user header"}, status=400)

    try:
        decoded_str = base64.b64decode(encoded_user).decode("utf-8")

        user_data = json.loads(decoded_str)
    except Exception as e:
        return JsonResponse({"error": "Invalid user data"}, status=400)

    return user_data


class BalanceApi(View):
    def get(self, request):
        user_data = get_user(request)

        user_id = user_data.get("id")
        if not user_id:
            return JsonResponse({"error": "User ID missing"}, status=400)

        user = TelegramUser.objects.filter(user_id=user_id).first()
        if not user:
            return JsonResponse({"error": "User not found"}, status=404)

        return JsonResponse({"balance": user.balance})


class UpdateUserApi(View):
    def get(self, request):
        try:

            user_id = request.GET.get('id', None)
            username = request.GET.get('username', None)
            first_name = request.GET.get('first_name', None)
            photo_url = request.GET.get('photo_url', None)

            searched_users = TelegramUser.objects.filter(
                user_id=user_id
            )

            print(user_id, username, first_name, photo_url)

            if searched_users.exists():
                searched_users.update(
                    username=username,
                    first_name=first_name,
                    photo_url=photo_url
                )
            else:
                TelegramUser.objects.create(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    photo_url=photo_url
                )

            return JsonResponse({'updated': [
                user_id,
                username,
                first_name,
                photo_url
            ]})
        except Exception as e:
            return JsonResponse({'error': str(e)})

def get_admin_id():
    return int(os.getenv("TELEGRAM_ADMIN_ID"))

@method_decorator(csrf_exempt, name='dispatch')
class SendVerifyApi(View):
    def post(self, request):
        user_data = get_user(request)
        amount = request.POST.get('amount')
        user_id = user_data.get("id")
        image = request.FILES.get('image')

        bot_token = settings.TELEGRAM_BOT_TOKEN
        admin_id = get_admin_id()

        # ✅ правильный порядок аргументов!
        threading.Thread(
            target=send_telegram_photo,
            args=(bot_token, admin_id, amount, user_id, image)
        ).start()

        return JsonResponse({'ok': True})
def check_admin_id(request):
    return JsonResponse({
        "settings_admin_id": getattr(settings, "TELEGRAM_ADMIN_ID", "❌ не найден"),
        "os_env_admin_id": os.getenv("TELEGRAM_ADMIN_ID", "❌ не найден"),
    })
