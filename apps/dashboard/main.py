from django.urls import reverse
from django.http import HttpResponseRedirect
from apps.merchant.models import Information, Service, Order, Bonus, LoyaltyPendingBonus
from apps.customer.models import Banner, Profile
from apps.product.models import SoldProduct, Ticket, Good, Phone, ProductItem
from decouple import config
from django.core.exceptions import ImproperlyConfigured
import requests
import urllib.parse
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views import View
from .forms import ServiceEditForm, InformationEditForm
from apps.dashboard.forms import BannerForm, NewsForm, NewsEditForm, BonusEditForm
from apps.customer.models import News
from datetime import date
from django.db.models import Q
from collections import defaultdict
from django.db.models import Sum
from decimal import Decimal
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


# Telegram Bot Settings (Safe for Build)
CHANNEL = int(config("CHANNEL", default="0"))
CHAT_ID = int(config("CHAT_ID", default="0"))
BOT_TOKEN = config("BOT_TOKEN", default="")
CHANNEL_USERNAME = "@openai_chat_gpt_robot"


def number_cutter(number):
    if number is not None:
        number = number.count()
        if number >= 100000:
            number = f"{round(number/1000000, 2)}M"
        elif number >= 1000:
            return f"{round(number/1000, 2)}K"
        else:
            return number
    else:
        return 0


def decimal_cutter(number):
    if number is not None:
        if number >= Decimal("100000"):
            return f"{round(number / Decimal('1000000'), 2)}M"
        elif number >= Decimal("1000"):
            return f"{round(number / Decimal('1000'), 2)}K"
        else:
            return number
    else:
        return 0


from django.db.models import Count, Sum, F


def dashboard(request):
    today = date.today()

    # Umumiy buyurtmalar obyekti
    all_orders = Order.objects.all()

    # --- 1. TEZKOR HARAKATLAR (Admin tasdiqlashi kerak bo'lgan narsalar) ---
    pending_orders_count = all_orders.filter(status="pending").count()  # Tovar borligini kutayotganlar
    check_pending_count = all_orders.filter(
        status="check_pending").count()  # To'lov cheki tekshirilishi kerak bo'lganlar
    pending_bonuses = LoyaltyPendingBonus.objects.filter(status="pending").count()
    # pending_b2b = B2BApplication.objects.filter(status="pending").count() # Agar model bo'lsa qo'shing

    # --- 2. BUGUNGI STATISTIKA ---
    order_today = all_orders.filter(created_at__date=today)
    order_today_count = order_today.count()

    # Bugungi daromad (faqat tasdiqlangan va yuborilganlar)
    revenue_today = order_today.filter(status__in=["approved", "sent"]).aggregate(total=Sum("total_amount"))[
                        "total"] or 0

    # --- 3. UMUMIY STATISTIKA ---
    customers_count = Profile.objects.count()
    customers_today_count = Profile.objects.filter(created_at__date=today).count()
    total_revenue = all_orders.filter(status__in=["approved", "sent"]).aggregate(total=Sum("total_amount"))[
                        "total"] or 0

    # --- 4. MAHSULOTLAR TAHLILI ---
    # Omborda kam qolganlar (Shoshilinch)
    low_stock_products = ProductItem.objects.filter(available_quantity__lt=10, active=True).order_by(
        'available_quantity')[:10]

    # Eng ko'p sotilganlar
    top_selling_products = SoldProduct.objects.values(
        "product__goods__name_uz",
        "product__phones__model_name_uz",
        "product__tickets__event_name_uz"
    ).annotate(total_qty=Sum("quantity")).order_by("-total_qty")[:10]

    # Grafik uchun ma'lumotlar
    chart_data = []
    for p in top_selling_products:
        title = p.get("product__goods__name_uz") or p.get("product__phones__model_name_uz") or p.get(
            "product__tickets__event_name_uz") or "Nomsiz"
        chart_data.append({"title": title, "total_quantity": p["total_qty"]})

    # So'nggi buyurtmalar
    recent_orders = all_orders.select_related("user").order_by("-created_at")[:15]

    return render(request, "base.html", {
        "pending_orders": pending_orders_count,
        "check_pending": check_pending_count,
        "pending_bonuses": pending_bonuses,
        "order_today_count": order_today_count,
        "revenue_today": revenue_today,
        "customers": customers_count,
        "customers_today": customers_today_count,
        "total_revenue": total_revenue,
        "recent": recent_orders,
        "chart_data": chart_data,
        "low_stock": low_stock_products,
        "comments": all_orders.exclude(comment="").order_by("-created_at")[:10],
    })


def get_first_image_url(product_item):
    first_image = product_item.images.first()
    return first_image.image.url if first_image else None


class InformationView(ListView):
    model = Information
    template_name = "dashboard/information/info_list.html"
    context_object_name = "infos"

    def get_queryset(self):
        return Information.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class InformationEditView(View):
    template_name = "dashboard/information/edit_info.html"

    def get(self, request, pk):
        info = get_object_or_404(Information, pk=pk)
        key = request.GET.get("key", None)
        form = InformationEditForm(instance=info)
        return render(
            request, self.template_name, {"form": form, "info": info, "key": key}
        )

    def post(self, request, pk):
        info = get_object_or_404(Information, pk=pk)
        form = InformationEditForm(request.POST, instance=info)

        if "edit" in request.POST and form.is_valid():
            form.save()
            return redirect("info-list")

        return render(request, self.template_name, {"form": form, "info": info})


class ServiceView(ListView):
    model = Service
    template_name = "dashboard/service/service_list.html"
    context_object_name = "services"

    def get_queryset(self):
        return Service.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch Bonus objects separately
        bonuses = Bonus.objects.all().order_by("pk")

        # Add the Bonus objects to the context
        context["bonuses"] = bonuses

        return context


class BannerView(ListView):
    model = Banner
    template_name = "dashboard/banner.html"
    context_object_name = "banners"
    form_class = BannerForm

    def get_queryset(self):
        return Banner.objects.all().order_by("-created_at")

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(
            request, self.template_name, {"banners": self.get_queryset(), "form": form}
        )

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("banner-list")
        else:
            return render(
                request,
                self.template_name,
                {"banners": self.get_queryset(), "form": form},
            )


class BannerActionView(View):
    def post(self, request, *args, **kwargs):
        if "action" not in request.POST:
            return render(
                request, "error.html", {"error_message": "Action not specified"}
            )

        action = request.POST.get("action")

        if action == "toggle":
            # Toggle the active status
            banner = get_object_or_404(Banner, pk=kwargs["pk"])
            banner.active = not banner.active
            banner.save()
        elif action == "delete":
            # Delete the banner
            banner = get_object_or_404(Banner, pk=kwargs["pk"])
            banner.delete()

        return redirect("banner-list")


class ServiceEditView(View):
    template_name = "dashboard/service/edit_service.html"

    def get(self, request, pk):
        service = get_object_or_404(Service, pk=pk)
        form = ServiceEditForm(instance=service)
        return render(request, self.template_name, {"form": form, "service": service})

    def post(self, request, pk):
        service = get_object_or_404(Service, pk=pk)
        if "edit" in request.POST:
            form = ServiceEditForm(request.POST, instance=service)
            if form.is_valid():
                form.save()
                return redirect("service-list")
        return render(request, self.template_name, {"form": form, "service": service})


class NewsListView(ListView):
    model = News
    template_name = "dashboard/news/news_list.html"
    context_object_name = "news"

    def get_queryset(self):
        return News.objects.all().order_by("-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NewsCreateView(View):
    template_name = "dashboard/news/news_create.html"

    def get(self, request):
        form = NewsForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("news-list")
        else:
            return render(request, self.template_name, {"form": form})


class NewsEditView(View):
    template_name = "dashboard/news/edit_delete_news.html"

    def get(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        form = NewsEditForm(instance=news)
        return render(request, self.template_name, {"form": form, "news": news})

    def post(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        form = NewsEditForm(request.POST, request.FILES, instance=news)

        if "edit" in request.POST:
            if form.is_valid():
                form.save()
                return redirect("news-list")
        if "delete" in request.POST:
            news = get_object_or_404(News, pk=pk)
            news.delete()
            return redirect("news-list")

        # If it's not a valid form or a delete action, render the form with the existing data
        return render(request, self.template_name, {"form": form, "news": news})


class OrdersView(DetailView):
    model = Profile
    template_name = "customer/orders/orders_list.html"

    def get_context_data(self, **kwargs):
        context = super(OrdersView, self).get_context_data(**kwargs)
        user = get_object_or_404(Profile, id=self.kwargs["pk"])
        orders = Order.objects.filter(user=user)

        if orders:
            context["orders"] = orders
            context["user"] = user
        else:
            context["no_orders_message"] = "Foydalanuvhi hali buyurtma qilmagan"

        return context

    def post(self, request, *args, **kwargs):
        order_id = self.kwargs["pk"]
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get("status")

        if new_status in dict(order.STATUS_CHOICES):
            order.status = new_status
            order.save()

        return HttpResponseRedirect(
            reverse("orders-list", kwargs={"pk": order.user.id})
        )


def bot(order):
    text4channel = f"""🔰 <b>Buyurtma holati:</b> #<i>YANGI</i>\n\n 🔢 <b>Buyurtma raqami:</b> <i>{order.id}</i>\n👤 <b>Mijoz ismi:</b> <i>{order.user.full_name}</i>\n📞 <b>Tel raqami:</b> <i>{order.user.phone_number}</i>\n🏠 <b>Manzili:</b> """
    for location in order.user.location.all():
        text4channel += f"{location.address}"
    text4channel += "\n🛒 <b>Mahsulotlar:</b> \n"
    for order_item in order.get_order_items():
        product_details = order.get_product_details(order_item, order_item)
        text4channel += f" 🟢 <i>{product_details}</i>\n"
    text4channel += f"📝 <b>Izoh:</b> <i>{order.comment}</i>\n📅 <b>Sana:</b> <i>{order.created_at.strftime('%Y-%m-%d %H:%M')}</i>\n💸 <b>Jami:</b> <i>{order.total_amount} ₩</i>\n\n⁉️ <u>To`lov amalga oshirilganligini tasdiqlaysizmi?</u>"
    inline_keyboard = [
        [
            {"text": "✅ Ha", "callback_data": f"yes|{order.id}"},
            {"text": "❌ Yo'q", "callback_data": f"no|{order.id}"},
        ]
    ]
    reply_markup = {
        "inline_keyboard": inline_keyboard,
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "selective": False,
        "row_width": 2,
    }
    encoded_reply_markup = urllib.parse.quote(json.dumps(reply_markup))
    encoded_text4channel = urllib.parse.quote(text4channel)
    url = f"""https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={encoded_text4channel}&reply_markup={encoded_reply_markup}&parse_mode=HTML"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error: {e}"


class BonusEditView(View):
    template_name = "dashboard/service/edit_bonus.html"

    def get(self, request, pk):
        bonus = get_object_or_404(Bonus, pk=pk)
        form = BonusEditForm(instance=bonus)
        return render(request, self.template_name, {"form": form, "bonus": bonus})

    def post(self, request, pk):
        bonus = get_object_or_404(Bonus, pk=pk)
        form = BonusEditForm(request.POST, instance=bonus)

        if form.is_valid():
            form.save()
            return redirect("service-list")

        return render(request, self.template_name, {"form": form, "bonus": bonus})
