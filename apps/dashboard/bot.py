from django.utils import timezone
from datetime import timedelta
from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from decouple import config
import telebot
from telebot import types

from apps.merchant.models import Order
from apps.product.models import SoldProduct

# ---------- SAFE ENV READ ----------
BOT_TOKEN = config("BOT_TOKEN", default=None)
CHANNEL = config("CHANNEL", default=None)

try:
    CHANNEL = int(CHANNEL) if CHANNEL is not None else None
except (ValueError, TypeError):
    CHANNEL = None

# ---------- SAFE BOT INIT ----------
bot = None
if BOT_TOKEN and ":" in BOT_TOKEN:
    try:
        bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
    except Exception:
        bot = None

hideBoard = types.ReplyKeyboardRemove()
extra_datas = {}

# ---------- WEBHOOK ENDPOINT ----------
@csrf_exempt
def index(request):
    if request.method == "GET":
        return HttpResponse("OK")

    if request.method == "POST" and bot:
        try:
            bot.process_new_updates(
                [telebot.types.Update.de_json(request.body.decode("utf-8"))]
            )
        except Exception:
            pass
    return HttpResponse(status=200)

# ---------- HANDLERS (ENABLED IF BOT INITIALIZED) ----------
if bot:
    @bot.message_handler(commands=["start"])
    def start(message: types.Message):
        pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith("yes|"))
    def approve_order(call):
        try:
            order = Order.objects.get(id=int(call.data.split("|")[-1]))
            order.status = "approved"
            order.save()
            if CHANNEL:
                bot.send_message(CHANNEL, f"Order #{order.id} approved")
        except Exception:
            pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith("no|"))
    def cancel_order(call):
        try:
            order = Order.objects.get(id=int(call.data.split("|")[-1]))
            order.status = "cancelled"
            order.save()
        except Exception:
            pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith("sent|"))
    def send_order(call):
        order_id = int(call.data.split("|")[-1])
        try:
            order = Order.objects.get(id=order_id)
            order.status = "sent"
            order.save()

            for order_item in order.orderitem.all():
                sold_product, _ = SoldProduct.objects.get_or_create(
                    product=order_item.product,
                    user=order.user,
                    defaults={
                        "quantity": 0,
                        "amount": 0,
                    },
                )
                sold_product.quantity += order_item.quantity
                sold_product.amount += (
                    order_item.product.new_price * order_item.quantity
                )
                sold_product.save()

        except Exception:
            pass
