import requests
import time
import hmac
import hashlib
import base64
import json
import os
from datetime import datetime
from .models import Transaction
from app.tg_util import send_transaction_info, send_transaction_done
from django.db.models import F

from django.conf import settings
from celery import shared_task

# File logging configuration
LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'moogold.log')

def log_to_file(level, message, exc_info=False):
    """
    Write log messages to file with timestamp
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {level.upper()}: {message}\n"
    
    try:
        with open(LOG_FILE_PATH, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            if exc_info:
                import traceback
                f.write(f"[{timestamp}] TRACEBACK:\n{traceback.format_exc()}\n")
    except Exception as e:
        # Fallback to console if file logging fails
        print(f"Failed to write to log file: {e}")
        print(log_entry)

def moogold_request(path: str, payload: dict, secret_key: str, partner_id: str):
    payload_json = json.dumps(payload)
    timestamp = str(int(time.time()))
    
    string_to_sign = payload_json + timestamp + path
    auth = hmac.new(secret_key.encode(), msg=string_to_sign.encode(), digestmod=hashlib.sha256).hexdigest()
    
    auth_basic = base64.b64encode(f'{partner_id}:{secret_key}'.encode()).decode()
    
    headers = {
        'timestamp': timestamp,
        'auth': auth,
        'Authorization': 'Basic ' + auth_basic,
        'Content-Type': 'application/json'
    }

    url = f'https://moogold.com/wp-json/v1/api/{path}'
    log_to_file('info', f"Making request to MooGold API: {url}")
    
    response = requests.post(url, data=payload_json, headers=headers)
    
    log_to_file('info', f"MooGold API response status: {response.status_code}")
    
    try:
        result = response.json()
        log_to_file('debug', f"MooGold API response: {result}")
        return result
    except Exception as e:
        log_to_file('error', f"Failed to parse JSON response: {e}")
        log_to_file('debug', f"Raw response: {response.text}")
        return response.text


@shared_task(bind=True)
def make_moogold_order(self, transaction_id):
    """
    Create an order in MooGold for a given transaction
    """
    log_to_file('info', f"Starting MooGold order creation for transaction {transaction_id}")
    
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        log_to_file('info', f"Found transaction: {transaction.id}, user: {transaction.user.user_id}")
        
        send_transaction_info(settings.TELEGRAM_BOT_TOKEN, transaction)
        
        # Prepare the order data
        order_data = {
            "category": transaction.merchandise.reseller_category,
            "product-id": transaction.merchandise.reseller_id,
            "quantity": str(transaction.quantity),
        }
        
        # Add dynamic inputs from transaction
        if transaction.inputs:
            log_to_file('debug', f"Adding transaction inputs: {transaction.inputs}")
            for input_item in transaction.inputs:
                for key, value in input_item.items():
                    order_data[key] = value
        
        # Create payload for MooGold API
        payload = {
            "path": "order/create_order",
            "data": order_data,
        }
        
        log_to_file('info', f"Prepared order payload: {payload}")
        
        # Make the request to MooGold
        result = moogold_request(
            path="order/create_order",
            payload=payload,
            secret_key=settings.MOOGOLD_SECRET_KEY,
            partner_id=settings.MOOGOLD_PARTNER
        )

        log_to_file('info', f"MooGold API result: {result}")
        
        # Update transaction with server response
        transaction.server_response = json.dumps(result) if isinstance(result, dict) else str(result)
        
        # Check if order was successful - handle both "true" and "processing" status
        if isinstance(result, dict):
            status = result.get('status', '').lower()
            has_order_id = 'order_id' in result
            
            log_to_file('info', f"Order status: {status}, has_order_id: {has_order_id}")

            # Success conditions: status is "true" or "processing", and we have an order_id
            if (status in ['true', 'processing']) and has_order_id:
                log_to_file('info', "Order accepted successfully")
                transaction.is_accepted = True
                
                if status == 'processing':
                    transaction.status = 'ontheway'
                    log_to_file('info', "Transaction status set to 'ontheway' (processing)")
                else:
                    transaction.status = 'ontheway'
                    log_to_file('info', "Transaction status set to 'ontheway'")
                
                if 'order_id' in result:
                    transaction.external_order_id = str(result['order_id'])
                    log_to_file('info', f"External order ID set: {transaction.external_order_id}")
                
                transaction.save()
                send_transaction_done(settings.TELEGRAM_BOT_TOKEN, transaction)
                
                return {
                    'success': True,
                    'message': 'Order created successfully',
                    'order_data': result,
                    'transaction_id': transaction.id,
                    'moogold_order_id': result.get('order_id'),
                    'moogold_status': status
                }
            else:
                log_to_file('warning', f"Order creation failed - invalid response: {result}")
                transaction.is_accepted = False
                transaction.status = 'failed'
                transaction.save()
                send_transaction_done(settings.TELEGRAM_BOT_TOKEN, transaction)
                
                return {
                    'success': False,
                    'message': 'Order creation failed - invalid response',
                    'error': result,
                    'transaction_id': transaction.id
                }
        else:
            # Non-dict response (likely error message)
            log_to_file('error', f"Non-dict response from MooGold: {result}")
            transaction.is_accepted = False
            transaction.status = 'failed'
            transaction.save()
            send_transaction_done(settings.TELEGRAM_BOT_TOKEN, transaction)
            
            return {
                'success': False,
                'message': 'Order creation failed',
                'error': result,
                'transaction_id': transaction.id
            }
            
    except Transaction.DoesNotExist:
        log_to_file('error', f'Transaction with id {transaction_id} not found')
        return {
            'success': False,
            'message': f'Transaction with id {transaction_id} not found'
        }
    except Exception as e:
        log_to_file('error', f'Error creating order for transaction {transaction_id}: {str(e)}', exc_info=True)
        
        # Log the error and update transaction status
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            transaction.server_response = f"Error: {str(e)}"
            transaction.is_accepted = False
            transaction.status = 'failed'
            transaction.save()
            send_transaction_done(settings.TELEGRAM_BOT_TOKEN, transaction)
            log_to_file('info', f"Transaction {transaction_id} marked as failed due to error")
        except Exception as save_error:
            log_to_file('error', f"Failed to update transaction {transaction_id} after error: {save_error}")
    
        return {
            'success': False,
            'message': f'Error creating order: {str(e)}',
            'transaction_id': transaction_id
        }


@shared_task(bind=True)
def refresh_status(self, transaction_id):
    """
    Refresh transaction status by checking order details from MooGold
    """
    log_to_file('info', f"Starting status refresh for transaction {transaction_id}")
    
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        log_to_file('info', f"Found transaction: {transaction.id}, user: {transaction.user.user_id}")
        
        # Check if we have an external order ID to query
        server_response = json.loads(transaction.server_response)
        order_id = server_response.get('order_id')

        if transaction.status in ["refunded", "incorrect-details"]:
            send_transaction_done(settings.TELEGRAM_BOT_TOKEN, transaction, already=True)

            return
        
        payload = {
            "path": "order/order_detail",
            "order_id": order_id
        }
        
        log_to_file('info', f"Prepared order detail payload: {payload}")
        
        
        # Make the request to MooGold
        result = moogold_request(
            path="order/order_detail",
            payload=payload,
            secret_key=settings.MOOGOLD_SECRET_KEY,
            partner_id=settings.MOOGOLD_PARTNER
        )

        log_to_file('info', f"MooGold order detail result: {result}")
        
        # Update transaction with refreshed server response
        if isinstance(result, dict):
            # Merge with existing server response if it exists
            try:
                existing_response = json.loads(transaction.server_response) if transaction.server_response else {}
            except (json.JSONDecodeError, TypeError):
                existing_response = {}
            
            # Add refresh result to server response with timestamp
            existing_response['refresh_result'] = result
            existing_response['last_refreshed'] = datetime.now().isoformat()
            transaction.server_response = json.dumps(existing_response)
        else:
            transaction.server_response = str(result)
        
        # Check order status and update transaction accordingly
        if isinstance(result, dict):
            order_status = result.get('order_status', '').lower()
            order_id = result.get('order_id')

            user = transaction.user
            
            
            log_to_file('info', f"Current order status: {order_status}, order_id: {order_id}")
            
            # Map MooGold order statuses to our transaction statuses
            old_status = transaction.status
            
            if order_status == 'completed':
                transaction.status = 'delivered'
                transaction.is_accepted = True
                log_to_file('info', f"Order completed - updating transaction to delivered")

            elif order_status == 'processing':
                transaction.status = 'ontheway'
                transaction.is_accepted = True
                log_to_file('info', f"Order still processing - keeping as ontheway")

            elif order_status == 'refunded':
                transaction.status = 'refunded'
                transaction.is_accepted = False

                user.balance += transaction.amount
                user.save()
                log_to_file('info', f"Order refunded - updating transaction to failed")
            
            elif order_status == 'incorrect-details':
                transaction.status = 'incorrect-details'
                transaction.is_accepted = False

                user.balance = F('balance') + transaction.amount
                user.save()
                log_to_file('info', f"Order has incorrect details - updating transaction to failed")
            else:
                transaction.status = 'failed'
                log_to_file('warning', f"Unknown order status: {order_status}")
                # Don't change status for unknown statuses
            
            # Log status change if it occurred
            if old_status != transaction.status:
                log_to_file('info', f"Transaction status changed: {old_status} -> {transaction.status}")
            else:
                log_to_file('info', f"Transaction status unchanged: {transaction.status}")
                
            transaction.save()
            send_transaction_done(settings.TELEGRAM_BOT_TOKEN, transaction)
            
            return {
                'success': True,
                'message': 'Status refreshed successfully',
                'order_data': result,
                'transaction_id': transaction.id,
                'old_status': old_status,
                'new_status': transaction.status,
                'moogold_order_status': order_status
            }
        else:
            # Non-dict response (likely error message)
            log_to_file('error', f"Non-dict response from MooGold order detail: {result}")
            transaction.save()
            
            return {
                'success': False,
                'message': 'Order detail request failed',
                'error': result,
                'transaction_id': transaction.id
            }
            
    except Transaction.DoesNotExist:
        log_to_file('error', f'Transaction with id {transaction_id} not found')
        return {
            'success': False,
            'message': f'Transaction with id {transaction_id} not found'
        }
    except Exception as e:
        log_to_file('error', f'Error refreshing status for transaction {transaction_id}: {str(e)}', exc_info=True)
        
        # Log the error but don't necessarily fail the transaction
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            # Add error info to server response without overwriting existing data
            try:
                existing_response = json.loads(transaction.server_response) if transaction.server_response else {}
            except (json.JSONDecodeError, TypeError):
                existing_response = {}
            
            existing_response['refresh_error'] = str(e)
            existing_response['refresh_error_timestamp'] = datetime.now().isoformat()
            transaction.server_response = json.dumps(existing_response)
            transaction.save()
            log_to_file('info', f"Added refresh error to transaction {transaction_id} server response")
        except Exception as save_error:
            log_to_file('error', f"Failed to update transaction {transaction_id} after refresh error: {save_error}")
    
        return {
            'success': False,
            'message': f'Error refreshing status: {str(e)}',
            'transaction_id': transaction_id
        }

@shared_task(bind=True)
def handle_moogold_callback(self, callback_data):
    """
    Handle callback from MooGold when order status changes
    """
    log_to_file('info', f"Handling MooGold callback: {callback_data}")
    
    try:
        order_id = callback_data.get('order_id')
        status = callback_data.get('status')
        message = callback_data.get('message')
        
        log_to_file('info', f"Callback details - order_id: {order_id}, status: {status}, message: {message}")
        
        if not order_id:
            log_to_file('error', 'No order_id in callback data')
            return {'success': False, 'message': 'No order_id in callback'}
        
        transaction = None
        
        # Try to find the transaction by checking server_response for order_id
        transactions = Transaction.objects.filter(
            server_response__icontains=f'"order_id": "{order_id}"'
        )
        
        if transactions.exists():
            transaction = transactions.first()
            log_to_file('info', f"Found transaction {transaction.id} for order_id {order_id}")
        else:
            log_to_file('error', f'Transaction not found for order_id {order_id}')
            return {'success': False, 'message': f'Transaction not found for order_id {order_id}'}
        
        # Update transaction status based on callback
        old_status = transaction.status
        
        if status == 'completed':
            transaction.status = 'delivered'
            transaction.is_accepted = True
            log_to_file('info', f"Transaction {transaction.id} marked as delivered")
        elif status == 'refunded' or status == 'incorrect-details':
            transaction.status = 'failed'
            transaction.is_accepted = False
            log_to_file('info', f"Transaction {transaction.id} marked as failed (status: {status})")
        else:
            transaction.status = 'ontheway'
            log_to_file('info', f"Transaction {transaction.id} status updated to ontheway")
        
        log_to_file('info', f"Transaction status changed: {old_status} -> {transaction.status}")
        
        # Update server response with callback info
        current_response = json.loads(transaction.server_response) if transaction.server_response else {}
        current_response['callback'] = callback_data
        transaction.server_response = json.dumps(current_response)
        transaction.save()
        
        log_to_file('info', f"Callback processed successfully for transaction {transaction.id}")
        
        return {
            'success': True,
            'message': 'Callback processed successfully',
            'transaction_id': transaction.id,
            'new_status': transaction.status
        }
        
    except Exception as e:
        log_to_file('error', f'Error processing callback: {str(e)}', exc_info=True)
        return {
            'success': False,
            'message': f'Error processing callback: {str(e)}'
        }