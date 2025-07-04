from django.views import View
from django.http import JsonResponse
from app.models import TelegramUser, Merchandise
from .models import Transaction
from django.db.models import F
from .tasks import make_moogold_order
import json
import base64


def get_user(request):
    encoded_user = request.headers.get("X-User-ID")
    if not encoded_user:
        return None

    try:
        decoded_str = base64.b64decode(encoded_user).decode("utf-8")
        return json.loads(decoded_str)
    except Exception:
        return None


class CreateTransactionApi(View):
    def get(self, request):
        try:
            # Получаем inputs и пользователя
            inputs_raw = request.GET.get("inputs")
            user_data = get_user(request)

            if not inputs_raw or not isinstance(user_data, dict):
                return JsonResponse({
                    "success": False,
                    "message": "O'yinchi ma'lumotlaringizni kiriting"
                }, status=400)

            # Собираем cart из всех query параметров, кроме 'inputs'
            try:
                cart = []
                for key, value in request.GET.items():
                    if key == "inputs":
                        continue
                    try:
                        qty = int(value)
                        cart.append({"slug": key, "qty": qty})
                    except ValueError:
                        return JsonResponse({
                            "success": False,
                            "message": f"Cartdagi element noto‘g‘ri formatda: {key}={value}"
                        }, status=400)
            except ValueError:
                return JsonResponse({
                    "success": False,
                    "message": "Cart noto‘g‘ri formatda"
                }, status=400)

            if not cart:
                return JsonResponse({
                    "success": False,
                    "message": "Savat bo‘sh"
                }, status=400)

            # Обработка inputs
            try:
                inputs = [
                    {k: v} for k, v in (item.split(":") for item in inputs_raw.split(","))
                ]
            except ValueError:
                return JsonResponse({
                    "success": False,
                    "message": "Inputs noto‘g‘ri formatda"
                }, status=400)

            # Получаем пользователя
            user = TelegramUser.objects.get(user_id=user_data.get("id"))

            total_amount = 0
            transaction_items = []

            for item in cart:
                slug = item["slug"].strip().lower()
                qty = item["qty"]

                try:
                    merchandise = Merchandise.objects.get(slug=slug, enabled=True)
                except Merchandise.DoesNotExist:
                    return JsonResponse({
                        "success": False,
                        "message": f"Bu mahsulot #{slug} topilmadi"
                    }, status=400)
                if not merchandise.server:
                    return JsonResponse({
                        "success": False,
                        "message": f"Mahsulot #{slug} uchun server tanlanmagan"
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

            # Создание транзакций
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

            # Обновляем баланс
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
                "message": traceback.format_exc()
            }, status=500)
