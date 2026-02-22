from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView
from apps.product.models import Phone, Ticket, Good, Category, SubCategory
from django.views import View
from django.views.generic.edit import CreateView
from .forms import (
    PhoneProductItemForm,
    TicketProductItemForm,
    GoodProductItemForm,
    PhoneCategoryCreateForm,
    TicketCategoryCreateForm,
    PhoneEditForm,
    GoodCategoryCreateForm,
    TicketEditForm,
    GoodEditForm,
    GoodMainCategoryCreateForm,
    CategoryEditForm,
    SubCategoryEditForm,
    CategoryCreateForm,
    SubCategoryCreateForm,
    GoodChildProductItemForm,
)
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

class PhoneListView(ListView):
    model = Phone
    template_name = "product/electronics/phone_list.html"  # your template name
    context_object_name = "phones"
    paginate_by = 10

    def get_queryset(self):
        return Phone.objects.all().order_by("pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PhoneCreateView(View):
    template_name = "product/electronics/phone_create.html"

    def get(self, request):
        form = PhoneProductItemForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = PhoneProductItemForm(
            request.POST, request.FILES
        )  # request.FILES ni o'tkazish
        if form.is_valid():
            form.save()
            return redirect("phone_list")
        return render(request, self.template_name, {"form": form})


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


class TicketListView(ListView):
    model = Ticket
    template_name = "product/tickets/ticket_list.html"  # your template name
    context_object_name = "tickets"
    paginate_by = 10

    def get_queryset(self):
        return Ticket.objects.all().order_by("pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any extra context here
        return context


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
        else:
            return render(request, self.template_name, {"form": form})


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


class GoodListView(ListView):
    model = Good
    template_name = "product/goods/good_list.html"
    context_object_name = "goods"
    paginate_by = 10  # Number of items per page

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        # Retrieve goods with related product and sub_category, and filter by name if a search query is provided
        goods = (
            Good.objects.filter(product__main=True)
            .select_related("product")
            .prefetch_related("sub_cat")
            .order_by("pk")
        )
        if query:
            goods = goods.filter(name_uz__icontains=query)
        return goods


class GoodCategoryCreateView(CreateView):
    model = SubCategory
    form_class = GoodCategoryCreateForm
    template_name = "product/goods/subcategory_create.html"
    success_url = reverse_lazy("good_create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Create New Good Category"
        return context

    def form_valid(self, form):
        form.instance.main_type = "f"
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


class GoodCreateView(View):
    template_name = "product/goods/good_create.html"

    def get(self, request):
        form = GoodProductItemForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = GoodProductItemForm(
            request.POST, request.FILES
        )  # request.FILES ni o'tkazish
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
        if request.method == "POST":
            form = GoodEditForm(request.POST, request.FILES, instance=good)
            if form.is_valid():
                form.save()
                return redirect("good-list")
        else:
            form = GoodEditForm(instance=good)
        return render(request, self.template_name, {"form": form, "good": good})


class ChildrenView(ListView):
    model = Good
    template_name = "product/goods/product_children.html"
    context_object_name = "children"
    form_class = GoodChildProductItemForm

    def get_queryset(self, request, pk):
        good = get_object_or_404(Good, pk=pk)
        product_type = good.product.product_type
        children = Good.objects.filter(
            product__product_type=product_type, product__main=False
        )
        return {"children": children, "good": good, 'type': product_type}

    def get(self, request, *args, **kwargs):
        obj = self.get_queryset(request, pk=kwargs["pk"])
        form = self.form_class(product_type=obj['type'])
        return render(
            request,
            self.template_name,
            {"children": obj["children"], "form": form, "good": obj["good"]},
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_queryset(request, pk=kwargs["pk"])
        form = self.form_class(request.POST, request.FILES, product_type=obj['type'])
        if form.is_valid():
            form.save()
            return redirect("add_product_child", pk=kwargs['pk'])
        else:
            return render(
                request,
                self.template_name,
                {"children": obj["children"], "form": form, "good": obj["good"]},
            )


class ChildActionView(View):
    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        parent_pk = kwargs.get("parent_pk")
        child_pk = kwargs.get("pk")

        if action == "toggle":
            child = get_object_or_404(Good, pk=child_pk)
            child.product.active = not child.product.active
            child.product.save()
        elif action == "delete":
            child = get_object_or_404(Good, pk=child_pk)
            child.delete()

        return redirect("add_product_child", pk=parent_pk)


class PhoneEditDeleteView(View):
    template_name = "product/electronics/edit_delete_phone.html"

    def get(self, request, pk):
        phone = get_object_or_404(Phone, pk=pk)
        form = PhoneEditForm(instance=phone)
        return render(request, self.template_name, {"form": form, "phone": phone})

    def post(self, request, pk):
        phone = get_object_or_404(Phone, pk=pk)
        if request.method == "POST":
            form = PhoneEditForm(request.POST, request.FILES, instance=phone)
            if form.is_valid():
                form.save()
                return redirect("phone_list")
        else:
            form = PhoneEditForm(instance=phone)
        return render(request, self.template_name, {"form": form, "phone": phone})


class PhoneDeleteView(View):
    def post(self, request, pk):
        phone = get_object_or_404(Phone, pk=pk)
        product_item = phone.product
        phone.delete()  # Delete the Phone instance
        product_item.delete()  # Delete the associated ProductItem
        return redirect("phone_list")  # Redirect to phone list


class TicketEditDeleteView(View):
    template_name = "product/tickets/edit_delete_ticket.html"

    def get(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        form = TicketEditForm(instance=ticket)
        categories = Category.objects.filter(main_type="t")
        return render(
            request,
            self.template_name,
            {"form": form, "ticket": ticket, "categories": categories},
        )

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        if request.method == "POST":
            form = TicketEditForm(request.POST, request.FILES, instance=ticket)
            if form.is_valid():
                form.save()
                return redirect("ticket-list")
        else:
            form = TicketEditForm(instance=ticket)
        return render(request, self.template_name, {"form": form, "ticket": ticket})


class TicketDeleteView(View):
    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        product_item = ticket.product
        ticket.delete()  # Delete the Phone instance
        product_item.delete()  # Delete the associated ProductItem
        return redirect("ticket-list")  # Redirect to phone list


class GoodDeleteView(View):
    def post(self, request, pk):
        ticket = get_object_or_404(Good, pk=pk)
        product_item = ticket.product
        ticket.delete()  # Delete the Phone instance
        product_item.delete()  # Delete the associated ProductItem
        return redirect("good-list")  # Redirect to phone list


class CategoryCreateView(CreateView):
    model = Category
    form_class = CategoryCreateForm
    template_name = "product/category_create.html"
    success_url = reverse_lazy("category-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Create New Good Category"
        return context

    def form_valid(self, form):
        return super().form_valid(form)


class CategoryListView(ListView):
    model = Category
    template_name = "product/category_list.html"  # your template name
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.all().order_by("pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class CategoryEditView(View):
    template_name = "product/category_edit.html"

    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        form = CategoryEditForm(instance=category)
        return render(
            request,
            self.template_name,
            {"form": form, "category": category},
        )

    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        form = CategoryEditForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            return redirect("category-list")
        return render(request, self.template_name, {"form": form, "category": category})


class CategoryDeleteView(View):
    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        category.delete()  # Delete the Phone instance
        return redirect("category-list")  # Redirect to phone list


class SubCategoryCreateView(CreateView):
    model = SubCategory
    form_class = SubCategoryCreateForm
    template_name = "product/goods/subcategory_create.html"
    success_url = reverse_lazy("subcategory-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Create New Good SubCategory"
        return context

    def form_valid(self, form):
        return super().form_valid(form)


class SubCategoryListView(ListView):
    model = SubCategory
    template_name = "product/goods/subcategory_list.html"  # your template name
    context_object_name = "subcategories"
    paginate_by = 10

    def get_queryset(self):
        return SubCategory.objects.all().order_by("pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class SubCategoryEditView(View):
    template_name = "product/goods/subcategory_edit.html"

    def get(self, request, pk):
        subcategory = get_object_or_404(SubCategory, pk=pk)
        form = SubCategoryEditForm(instance=subcategory)
        return render(
            request,
            self.template_name,
            {"form": form, "subcategory": subcategory},
        )

    def post(self, request, pk):
        subcategory = get_object_or_404(SubCategory, pk=pk)
        form = SubCategoryEditForm(request.POST, request.FILES, instance=subcategory)
        if form.is_valid():
            form.save()
            return redirect("subcategory-list")
        return render(
            request, self.template_name, {"form": form, "subcategory": subcategory}
        )


class SubCategoryDeleteView(View):
    def post(self, request, pk):
        subcategory = get_object_or_404(SubCategory, pk=pk)
        subcategory.delete()  # Delete the Phone instance
        return redirect("subcategory-list")  # Redirect to phone list