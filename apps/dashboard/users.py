from apps.customer.models import Profile, Location
from apps.merchant.models import Order, OrderItem, Service
from django.views.generic import ListView, DetailView
from django.shortcuts import render, redirect, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView
from django.db.models import Subquery, OuterRef
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.db.models import Prefetch, Q, Count


class UserListView(ListView):
    model = Profile
    template_name = "customer/users/users_list.html"
    context_object_name = "users"
    paginate_by = 10

    def get_queryset(self):
        # Fetch the profiles along with their active locations
        profiles = Profile.objects.select_related("origin").order_by("-pk")
        return profiles

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch active locations for each profile
        profiles = self.get_queryset()
        active_locations = {}
        for profile in profiles:
            profile_locations = Location.objects.filter(user=profile, active=True)
            active_locations[profile] = profile_locations

        context["active_locations"] = active_locations
        return context


class BlockActivateUserView(View):
    def get(self, request, pk):
        user = get_object_or_404(Profile, id=pk)
        user.origin.is_active = not user.origin.is_active
        user.origin.save()
        return redirect("users-list")


class UserOrdersView(DetailView):
    model = Profile
    template_name = "customer/users/user_orders_list.html"

    def get_context_data(self, **kwargs):
        context = super(UserOrdersView, self).get_context_data(**kwargs)
        orders = Order.objects.filter(user__id=self.kwargs["pk"])
        user = Profile.objects.get(id=self.kwargs["pk"])
        if orders:
            context["orders"] = orders
            context["user"] = user
        else:
            context["no_orders_message"] = "Foydalanuvhi hali buyurtma qilmagan"
        return context


class UserOrderDetailView(DetailView):
    model = Order
    template_name = "customer/users/user_order_detail.html"

    def get_context_data(self, **kwargs):
        context = super(UserOrderDetailView, self).get_context_data(**kwargs)
        order = Order.objects.get(id=self.kwargs["pk"])
        order_items = OrderItem.objects.filter(order__id=self.kwargs["pk"])
        user = order.user
        cargo = Service.objects.all().first().delivery_fee

        order_items_data = []  # List to store data for each OrderItem

        for order_item in order_items:
            product_type, details = self.get_product_type(order_item.product)
            first_image_url = self.get_first_image_url(order_item.product)
            # Calculate total price for each OrderItem
            if order_item.product.new_price:
                total_price = order_item.quantity * order_item.product.new_price
            elif order_item.product.old_price:
                total_price = order_item.quantity * order_item.product.old_price
            else:
                total_price = 0

            # Add data for each OrderItem to the list
            order_items_data.append(
                {
                    "order_item": order_item,
                    "product_type": product_type,
                    "details": details,
                    "total_price": total_price,
                    "first_image_url": first_image_url,
                }
            )

        if order_items:
            context["order_items_data"] = order_items_data
            context["user"] = user
            context["order"] = order
            context["cargo"] = cargo
        else:
            context["no_orders_message"] = "This user has no orders."

        return context

    def get_first_image_url(self, product_item):
        # Get the first image URL for the product
        first_image = product_item.images.first()
        return first_image.image.url if first_image else None

    def get_product_type(self, product_item):
        if hasattr(product_item, "phones"):
            return "Phone", {
                "model_name": product_item.phones.model_name,
                "ram": product_item.phones.get_ram_display(),
                "storage": product_item.phones.get_storage_display(),
                "color": product_item.phones.get_color_display(),
                "condition": product_item.phones.get_condition_display(),
            }
        elif hasattr(product_item, "tickets"):
            x = "Ticket", {
                "event_name": product_item.tickets.event_name,
                "event_date": product_item.tickets.event_date,
                "category": (
                    product_item.tickets.category.name
                    if product_item.tickets.category
                    else "Bilet"
                ),
                "price": (
                    product_item.new_price
                    if product_item.new_price
                    else product_item.old_price
                ),
            }
            return x
        elif hasattr(product_item, "goods"):
            return "Good", {
                "name": product_item.goods.name,
                "ingredients": product_item.goods.ingredients,
                "expire_date": product_item.goods.expire_date,
                "sub_cat": (
                    product_item.goods.sub_cat.name
                    if product_item.goods.sub_cat
                    else None
                ),
            }
        return None, None


class OrdersListView(ListView):
    template_name = "customer/orders/orders_list.html"
    context_object_name = "orders"
    paginate_by = 10
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        # Retrieve goods with related product and sub_category, and filter by name if a search query is provided
        order = (
            Order.objects.select_related("user").order_by("-id")
        )
        if query:
            order = order.filter(Q(user__full_name__icontains=query) | Q(id__icontains=query))
        return order


def update_order_status(request, pk):
    order = get_object_or_404(Order, id=pk)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(order.STATUS_CHOICES):
            order.status = new_status
            order.save()

    return HttpResponseRedirect(reverse("all-orders-list"))


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm
from django.contrib import messages


def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                next_url = request.POST.get("next", "dashboard")
                if next_url == "":
                    return redirect("dashboard")
                    # Agar 'next' mavjud bo'lmasa, 'dashboard'ga yo'naltiradi
                return redirect(next_url)
            else:
                messages.error(request, "Login yoki parol xato")
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})


# logout page
def user_logout(request):
    logout(request)
    return redirect("login_page")


def order_update_status(request, pk):
    if request.method == "POST":
        order = get_object_or_404(Order, id=pk)
        new_status = request.POST.get('status')
        if new_status:
            order.status = new_status
            order.save()

    # Qayerga qaytishni ko'rsatish (buyurtmalar ro'yxati sahifasiga)
    return redirect(request.META.get('HTTP_REFERER', 'user-orders-list'))