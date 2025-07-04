from django.views import View
from django.http import JsonResponse
from app.models import TelegramUser, Merchandise
from .models import Transaction
from django.db.models import F
from .tasks import make_moogold_order
import json
import base64
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

def get_user(request):
    encoded_user = (
        request.headers.get("X-User-ID") or
        request.META.get("HTTP_X_USER_ID")  # fallback
    )
    print("DEBUG: encoded_user =", encoded_user)  # временно
    if not encoded_user:
        return None

    try:
        decoded_str = base64.b64decode(encoded_user).decode("utf-8")
        return json.loads(decoded_str)
    except Exception:
        return None

@method_decorator(csrf_exempt, name='dispatch')
class CreateTransactionApi(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            inputs_raw = data.get("inputs")
            user_data = data.get("user")  # user теперь в теле, не в заголовке
            cart = data.get("cart", [])

            if not inputs_raw or not isinstance(user_data, dict):
                return JsonResponse({
                    "success": False,
                    "message": "O'yinchi ma'lumotlaringizni kiriting",
                    "debug": {
                        "inputs_raw": inputs_raw,
                        "user_data": user_data
                    }
                }, status=400)

            # Обработка inputs
            try:
                inputs = []
                for item in inputs_raw.split(","):
                    if ":" not in item:
                        continue
                    k, v = item.split(":", 1)
                    inputs.append({k: v})
            except Exception:
                return JsonResponse({
                    "success": False,
                    "message": "Inputs noto‘g‘ri formatda"
                }, status=400)

            # Получаем пользователя
            user = TelegramUser.objects.get(user_id=user_data.get("id"))

            total_amount = 0
            transaction_items = []

            for item in cart:
                slug = item.get("slug", "").strip().lower()
                qty = int(item.get("qty", 1))

                merchandise = Merchandise.objects.filter(slug=slug, enabled=True).first()
                if not merchandise:
                    return JsonResponse({
                        "success": False,
                        "message": f"Mahsulot topilmadi: {slug}"
                    }, status=400)

                price = int(merchandise.price)
                amount = price * qty
                total_amount += amount

                transaction_items.append({
                    "merchandise": merchandise,
                    "quantity": qty,
                    "amount": amount
                })

            if user.balance < total_amount:
                return JsonResponse({
                    "success": False,
                    "message": "Hisobingizda mablag' yetarli emas!"
                }, status=400)

            created_transactions = []
            for item in transaction_items:
                transaction = Transaction.objects.create(
                    user=user,
                    merchandise=item["merchandise"],
                    quantity=item["quantity"],
                    inputs=inputs,
                    amount=item["amount"],
                    is_accepted=True
                )
                make_moogold_order.delay(transaction.id)
                created_transactions.append(transaction)

            user.balance = F("balance") - total_amount
            user.save()

            return JsonResponse({
                "success": True,
                "message": "✅ Buyurtmangiz muvaffaqiyatli qabul qilindi!",
                "transaction_ids": [t.id for t in created_transactions],
                "total_amount": str(total_amount)
            })

        except TelegramUser.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "User not found"
            }, status=404)

        except Exception as e:
            import traceback
            return JsonResponse({
                "success": False,
                "message": "Xatolik yuz berdi",
                "debug": traceback.format_exc()
            }, status=500)