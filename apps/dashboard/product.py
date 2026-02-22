from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView
from django.views import View
from django.db.models import Q

from apps.product.models import Phone, Ticket, Good, Category, ProductItem
from .forms import (
    PhoneProductItemForm,
    TicketProductItemForm,
    GoodProductItemForm,
    PhoneCategoryCreateForm,
    TicketCategoryCreateForm,
    PhoneEditForm,
    TicketEditForm,
    GoodEditForm,
    GoodMainCategoryCreateForm,
    CategoryEditForm,
    CategoryCreateForm,
    GoodChildProductItemForm,
)

# ==========================================
# 1. PHONE (ELECTRONICS) VIEWS
# ==========================================

class PhoneListView(ListView):
    model = Phone
    template_name = "product/electronics/phone_list.html"
    context_object_name = "phones"
    paginate_by = 10

    def get_queryset(self):
        return Phone.objects.all().select_related('product', 'category').order_by("-pk")


class PhoneCreateView(View):
    template_name = "product/electronics/phone_create.html"

    def get(self, request):
        form = PhoneProductItemForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = PhoneProductItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("phone_list")
        return render(request, self.template_name, {"form": form})


class PhoneEditDeleteView(View):
    template_name = "product/electronics/edit_delete_phone.html"

    def get(self, request, pk):
        phone = get_object_or_404(Phone, pk=pk)
        form = PhoneEditForm(instance=phone)
        return render(request, self.template_name, {"form": form, "phone": phone})

    def post(self, request, pk):
        phone = get_object_or_404(Phone, pk=pk)
        form = PhoneEditForm(request.POST, request.FILES, instance=phone)
        if form.is_valid():
            form.save()
            return redirect("phone_list")
        return render(request, self.template_name, {"form": form, "phone": phone})


# ==========================================
# 2. TICKET VIEWS
# ==========================================

class TicketListView(ListView):
    model = Ticket
    template_name = "product/tickets/ticket_list.html"
    context_object_name = "tickets"
    paginate_by = 10

    def get_queryset(self):
        return Ticket.objects.all().select_related('product', 'category').order_by("-pk")


class TicketCreateView(View):
    template_name = "product/tickets/ticket_create.html"

    def get(self, request):
        form = TicketProductItemForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = TicketProductItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("ticket-list")
        return render(request, self.template_name, {"form": form})


class TicketEditDeleteView(View):
    template_name = "product/tickets/edit_delete_ticket.html"

    def get(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        form = TicketEditForm(instance=ticket)
        return render(request, self.template_name, {"form": form, "ticket": ticket})

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        form = TicketEditForm(request.POST, request.FILES, instance=ticket)
        if form.is_valid():
            form.save()
            return redirect("ticket-list")
        return render(request, self.template_name, {"form": form, "ticket": ticket})


# ==========================================
# 3. GOOD (OZIQ-OVQAT) VIEWS
# ==========================================

class GoodListView(ListView):
    model = Good
    template_name = "product/goods/good_list.html"
    context_object_name = "goods"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        # Oldingi sub_cat o'rniga category select_related qilindi
        goods = (
            Good.objects.filter(product__main=True)
            .select_related("product", "category")
            .order_by("-pk")
        )
        if query:
            goods = goods.filter(name_uz__icontains=query)
        return goods


class GoodCreateView(View):
    template_name = "product/goods/good_create.html"

    def get(self, request):
        form = GoodProductItemForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = GoodProductItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("good-list")
        return render(request, self.template_name, {"form": form})


class GoodEditDeleteView(View):
    template_name = "product/goods/good_edit.html"

    def get(self, request, pk):
        good = get_object_or_404(Good, pk=pk)
        form = GoodEditForm(instance=good)
        return render(request, self.template_name, {"form": form, "good": good})

    def post(self, request, pk):
        good = get_object_or_404(Good, pk=pk)
        form = GoodEditForm(request.POST, request.FILES, instance=good)
        if form.is_valid():
            form.save()
            return redirect("good-list")
        return render(request, self.template_name, {"form": form, "good": good})


# --- Mahsulot Variantlari (Children) ---

class ChildrenView(View):
    template_name = "product/goods/product_children.html"
    form_class = GoodChildProductItemForm

    def get_data(self, pk):
        good = get_object_or_404(Good, pk=pk)
        product_type = good.product.product_type
        children = Good.objects.filter(
            product__product_type=product_type, product__main=False
        ).select_related('product')
        return good, children, product_type

    def get(self, request, pk):
        good, children, p_type = self.get_data(pk)
        form = self.form_class(product_type=p_type)
        return render(request, self.template_name, {
            "children": children, "form": form, "good": good
        })

    def post(self, request, pk):
        good, children, p_type = self.get_data(pk)
        form = self.form_class(request.POST, request.FILES, product_type=p_type)
        if form.is_valid():
            form.save()
            return redirect("add_product_child", pk=pk)
        return render(request, self.template_name, {
            "children": children, "form": form, "good": good
        })


# ==========================================
# 4. CATEGORY MANAGEMENT VIEWS
# ==========================================

class CategoryListView(ListView):
    model = Category
    template_name = "product/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.all().order_by("-pk")


class CategoryCreateView(CreateView):
    model = Category
    form_class = CategoryCreateForm
    template_name = "product/category_create.html"
    success_url = reverse_lazy("category-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Yangi kategoriya yaratish"
        return context


class CategoryEditView(View):
    template_name = "product/category_edit.html"

    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        form = CategoryEditForm(instance=category)
        return render(request, self.template_name, {"form": form, "category": category})

    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        form = CategoryEditForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            return redirect("category-list")
        return render(request, self.template_name, {"form": form, "category": category})


# ==========================================
# 5. DELETE ACTIONS (Takrorlanishni kamaytirish uchun)
# ==========================================

class BaseDeleteView(View):
    model = None
    success_url = None

    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        # Agar mahsulot bo'lsa, bog'liq ProductItemni ham o'chiradi
        if hasattr(obj, 'product'):
            p_item = obj.product
            obj.delete()
            p_item.delete()
        else:
            obj.delete()
        return redirect(self.success_url)

class PhoneDeleteView(BaseDeleteView):
    model = Phone
    success_url = "phone_list"

class TicketDeleteView(BaseDeleteView):
    model = Ticket
    success_url = "ticket-list"

class GoodDeleteView(BaseDeleteView):
    model = Good
    success_url = "good-list"

class CategoryDeleteView(BaseDeleteView):
    model = Category
    success_url = "category-list"

class ChildActionView(View):
    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        parent_pk = kwargs.get("parent_pk")
        child_pk = kwargs.get("pk")
        child = get_object_or_404(Good, pk=child_pk)

        if action == "toggle":
            child.product.active = not child.product.active
            child.product.save()
        elif action == "delete":
            p_item = child.product
            child.delete()
            p_item.delete()

        return redirect("add_product_child", pk=parent_pk)

# --- Eskirgan (SubCategory) Viewlar butunlay olib tashlandi ---




class PhoneCategoryCreateView(CreateView):
    model = Category
    form_class = PhoneCategoryCreateForm
    template_name = "product/category_create.html"
    success_url = reverse_lazy("create_phone")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Create New Phone Category"
        return context

    def form_valid(self, form):
        form.instance.main_type = "p"
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


class TicketCategoryCreateView(CreateView):
    model = Category
    form_class = TicketCategoryCreateForm
    template_name = "product/category_create.html"
    success_url = reverse_lazy("ticket_create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Create New Ticket Category"
        return context

    def form_valid(self, form):
        form.instance.main_type = "t"
        return super().form_valid(form)



class GoodMainCategoryCreateView(CreateView):
    model = Category
    form_class = GoodMainCategoryCreateForm
    template_name = "product/goods/category_create.html"
    success_url = reverse_lazy("good_subcategory")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Create New Good Category"
        return context

    def form_valid(self, form):
        form.instance.main_type = "f"
        return super().form_valid(form)