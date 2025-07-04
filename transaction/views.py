from django.views import View
from django.http import JsonResponse
from app.models import TelegramUser, Merchandise
from .models import Transaction
from django.db.models import F

import json
import base64
from .tasks import make_moogold_order


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


class CreateTransactionApi(View):
    def get(self, request):
        try:
            # Get parameters from request
            inputsRaw = request.GET.get("inputs")
            cartRaw = request.GET.get("cart")
            userJson = get_user(request)
            
            
            if not all([inputsRaw, cartRaw, userJson]):
                return JsonResponse({
                    'success': False,
                    'message': 'O\'yinchi ma\'lumotlaringizni kiriting'
                }, status=400)
            
            # Parse inputs and cart
            inputs = [{k: v} for k, v in (item.split(":") for item in inputsRaw.split(","))]
            cart = [{"id": k, "qty": v} for k, v in (item.split(":") for item in cartRaw.split(","))]
            
            print(f"Inputs: {inputs}")
            print(f"Cart: {cart}")
            print(f"User: {userJson}")
            
            
            user = TelegramUser.objects.get(user_id=userJson.get("id"))
            
            total_amount = 0
            transaction_items = []
            
            for cart_item in cart:
                merchandise_id = cart_item.get('id')
                quantity = int(cart_item.get('qty', 1))
                
                try:
                    merchandise = Merchandise.objects.get(
                        id=merchandise_id,
                        enabled=True
                    )
                except Merchandise.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': f'Bu mahsulot #{merchandise_id} topilmadi'
                    }, status=400)
                
                
                item_price = int(merchandise.price)
                item_total = item_price * quantity
                total_amount += item_total
                
                transaction_items.append({
                    'merchandise': merchandise,
                    'quantity': quantity,
                    'amount': item_total
                })
            
            if user.balance < total_amount:
                return JsonResponse({
                    'success': False,
                    'message': 'Hisobingizda mablag\' yetarli emas!'
                }, status=400)
            
            created_transactions = []
            
            for item in transaction_items:
                new_transaction = Transaction.objects.create(
                    user=user,
                    merchandise=item['merchandise'],
                    quantity=item['quantity'],
                    inputs=inputs,
                    amount=item['amount'],
                    is_accepted=True
                )

                make_moogold_order.delay(new_transaction.id)
                created_transactions.append(new_transaction)
                
            user.balance = F('balance') - total_amount
            user.save()
            
            return JsonResponse({
                'success': True,
                'message': '✅ Buyurtmangiz muvaffaqiyatli qabul qilindi!',
                'transaction_ids': [t.id for t in created_transactions],
                'total_amount': str(total_amount)
            })
            
        except TelegramUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User not found'
            }, status=404)
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': f'Invalid data format: {str(e)}'
            }, status=400)
            
        except Exception as e:
            print(f"Transaction error: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Qandaydir xatolik yuz berdi, qaytadan urinib ko\'ring'
            }, status=500)
