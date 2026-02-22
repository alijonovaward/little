from typing import Any
from django import forms
from django.forms import ClearableFileInput
from apps.product.models import (
    Phone,
    ProductItem,
    Image,
    Ticket,
    Good,
    Category,
)
from django.core.validators import MinValueValidator
from apps.customer.models import News, Banner
from apps.merchant.models import Information, Service, Bonus, SocialMedia
from django.utils import timezone
from ckeditor.widgets import CKEditorWidget


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("attrs", {})
        kwargs["attrs"].update({"class": "form-control", "multiple": True})
        super(MultipleFileInput, self).__init__(*args, **kwargs)


class MultipleFileField(forms.ImageField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


# --- Phone Forms ---

class PhoneProductItemForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(main_type="p"),
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Kategoriyasi",
    )
    # ... (desc_uz, desc_ru, etc fields qolgan qismi bir xil)
    desc_uz = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control"}), label="Ta`rif UZ")
    desc_ru = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control"}), label="Ta`rif RU")
    desc_en = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control"}), label="Ta`rif EN")
    desc_ko = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control"}), label="Ta`rif KR")
    new_price = forms.DecimalField(decimal_places=0, max_digits=10, required=False,
                                   widget=forms.NumberInput(attrs={"class": "form-control"}),
                                   label="Chegirmadagi narxi")
    old_price = forms.DecimalField(decimal_places=0, max_digits=10, required=False,
                                   widget=forms.NumberInput(attrs={"class": "form-control"}), label="Narxi")
    weight = forms.DecimalField(decimal_places=1, max_digits=10, required=False,
                                widget=forms.NumberInput(attrs={"class": "form-control"}),
                                label="Maxsulot og`irligi (KG)", initial=1)
    available_quantity = forms.IntegerField(min_value=0, widget=forms.NumberInput(attrs={"class": "form-control"}),
                                            label="Mavjud miqdori")
    active = forms.BooleanField(widget=forms.CheckboxInput(attrs={"class": "form-check-input"}), initial=True,
                                required=False)
    images = MultipleFileField()

    class Meta:
        model = Phone
        fields = ["model_name", "ram", "storage", "category", "color", "condition"]
        widgets = {
            "model_name": forms.TextInput(attrs={"class": "form-control"}),
            "ram": forms.Select(attrs={"class": "form-control"}),
            "storage": forms.Select(attrs={"class": "form-control"}),
            "color": forms.Select(attrs={"class": "form-control"}),
            "condition": forms.Select(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        phone = super().save(commit=False)
        product_item = ProductItem.objects.create(
            weight=self.cleaned_data.get("weight") or 1,
            desc_uz=self.cleaned_data["desc_uz"],
            desc_ru=self.cleaned_data["desc_ru"],
            desc_en=self.cleaned_data["desc_en"],
            desc_ko=self.cleaned_data["desc_ko"],
            new_price=self.cleaned_data["new_price"],
            old_price=self.cleaned_data.get("old_price"),
            available_quantity=self.cleaned_data["available_quantity"],
            active=self.cleaned_data["active"],
        )
        phone.product = product_item
        phone.category = self.cleaned_data["category"]
        if commit:
            phone.save()
            for img in self.files.getlist("images"):
                Image.objects.create(image=img, name=f"{phone.model_name}_{img.name}", product=product_item)
        return phone


# --- Ticket Forms ---

class TicketProductItemForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(main_type="t"),
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Kategoriya",
    )
    # ... (boshqa fieldlar bir xil)
    event_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "date", "class": "form-control"}),
                                     label="Hodisa sanasi")
    desc_uz = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control"}))
    new_price = forms.DecimalField(decimal_places=0, max_digits=10)
    available_quantity = forms.IntegerField(min_value=0)
    images = MultipleFileField()

    class Meta:
        model = Ticket
        fields = ["event_name_uz", "event_name_ru", "event_name_en", "event_name_ko"]

    def save(self, commit=True):
        ticket = super().save(commit=False)
        product_item = ProductItem.objects.create(
            desc_uz=self.cleaned_data.get("desc_uz", ""),
            new_price=self.cleaned_data["new_price"],
            available_quantity=self.cleaned_data["available_quantity"],
        )
        ticket.product = product_item
        ticket.category = self.cleaned_data["category"]
        if commit:
            ticket.save()
            for img in self.files.getlist("images"):
                Image.objects.create(image=img, name=f"{ticket.event_name_uz}_{img.name}", product=product_item)
        return ticket


# --- Good (Oziq-ovqat) Forms - BU YERDA O'ZGARISH KATTA ---

class GoodProductItemForm(forms.ModelForm):
    # Klasslar Sherah shabloniga moslandi
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(main_type="f"),
        widget=forms.Select(attrs={"class": "sherah-wc__form-input"}),
        label="Kategoriyasi",
    )
    new_price = forms.DecimalField(
        widget=forms.NumberInput(attrs={"class": "sherah-wc__form-input", "placeholder": "0"}))
    discount_price = forms.DecimalField(required=False, widget=forms.NumberInput(
        attrs={"class": "sherah-wc__form-input", "placeholder": "0"}))
    b2b_price = forms.DecimalField(required=False, widget=forms.NumberInput(
        attrs={"class": "sherah-wc__form-input", "placeholder": "0"}))
    available_quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={"class": "sherah-wc__form-input", "placeholder": "0"}))
    weight = forms.FloatField(required=False,
                              widget=forms.NumberInput(attrs={"class": "sherah-wc__form-input", "placeholder": "0"}))
    measure = forms.ChoiceField(choices=ProductItem.CHOICES,
                                widget=forms.Select(attrs={"class": "sherah-wc__form-input"}))

    # Text inputlar
    name_uz = forms.CharField(
        widget=forms.TextInput(attrs={"class": "sherah-wc__form-input", "placeholder": "Nomi UZ"}))
    name_ru = forms.CharField(required=False, widget=forms.TextInput(
        attrs={"class": "sherah-wc__form-input", "placeholder": "Nomi RU"}))
    name_en = forms.CharField(required=False, widget=forms.TextInput(
        attrs={"class": "sherah-wc__form-input", "placeholder": "Nomi EN"}))
    name_ko = forms.CharField(required=False, widget=forms.TextInput(
        attrs={"class": "sherah-wc__form-input", "placeholder": "Nomi KO"}))

    # Textarealar
    desc_uz = forms.CharField(required=False,
                              widget=forms.Textarea(attrs={"class": "sherah-wc__form-input", "rows": "3"}))
    desc_ru = forms.CharField(required=False,
                              widget=forms.Textarea(attrs={"class": "sherah-wc__form-input", "rows": "3"}))
    desc_en = forms.CharField(required=False,
                              widget=forms.Textarea(attrs={"class": "sherah-wc__form-input", "rows": "3"}))
    desc_ko = forms.CharField(required=False,
                              widget=forms.Textarea(attrs={"class": "sherah-wc__form-input", "rows": "3"}))
    active = forms.BooleanField(required=False, initial=True)
    main = forms.BooleanField(required=False, initial=False)
    # MultipleFileField o'rniga bitta ImageField:
    image = forms.ImageField(label="Mahsulot rasmi",
                             widget=forms.FileInput(attrs={"class": "form-control border-dark"}))


    class Meta:
        model = Good
        fields = ["name_uz", "name_ru", "name_en", "name_ko", "ingredients"]

    def save(self, commit=True):
        good = super().save(commit=False)
        # sub_cat o'rniga category ga saqlaymiz
        good.category = self.cleaned_data.get("category")

        product_item = ProductItem.objects.create(
            desc_uz=self.cleaned_data.get("desc_uz", ""),
            measure=self.cleaned_data["measure"],
            new_price=self.cleaned_data["new_price"],
            available_quantity=self.cleaned_data["available_quantity"],
        )
        good.product = product_item
        if commit:
            good.save()
            for img in self.files.getlist("images"):
                Image.objects.create(image=img, name=f"{good.name_uz}_{img.name}", product=product_item)
        return good


class GoodEditForm(forms.ModelForm):
    # sub_cat o'rniga category
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(main_type="f"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Kategoriyasi"
    )
    # ... (boshqa edit fieldlar)
    old_price = forms.DecimalField(decimal_places=0, max_digits=10,
                                   widget=forms.NumberInput(attrs={"class": "form-control"}))
    new_price = forms.DecimalField(decimal_places=0, max_digits=10,
                                   widget=forms.NumberInput(attrs={"class": "form-control"}))

    class Meta:
        model = Good
        fields = ["name_uz", "name_ru", "name_ko", "name_en", "expire_date", "category", "ingredients"]

    def __init__(self, *args, **kwargs):
        super(GoodEditForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.product:
            p = self.instance.product
            self.fields["old_price"].initial = p.old_price
            self.fields["new_price"].initial = p.new_price

    def save(self, commit=True):
        good = super().save(commit=False)
        # Modelda sub_cat o'rniga category ishlatilgan bo'lishi kerak
        good.category = self.cleaned_data['category']

        product_item = good.product
        product_item.new_price = self.cleaned_data["new_price"]
        product_item.old_price = self.cleaned_data["old_price"]

        if commit:
            product_item.save()
            good.save()
            # Image logic...
        return good

from django.core.files.uploadedfile import InMemoryUploadedFile


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = "__all__"
        widgets = {
            "title_uz": forms.TextInput(attrs={"class": "form-control"}),
            "title_ru": forms.TextInput(attrs={"class": "form-control"}),
            "title_en": forms.TextInput(attrs={"class": "form-control"}),
            "title_ko": forms.TextInput(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "description_uz": forms.Textarea(attrs={"class": "form-control"}),
            "description_ru": forms.Textarea(attrs={"class": "form-control"}),
            "description_en": forms.Textarea(attrs={"class": "form-control"}),
            "description_ko": forms.Textarea(attrs={"class": "form-control"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "title_uz": "Sarlovha (UZ)",
            "title_ru": "Sarlovha (RU)",
            "title_en": "Sarlovha (EN)",
            "title_ko": "Sarlovha (KO)",
            "description_uz": "Tasnif (UZ)",
            "description_ru": "Tasnif (RU)",
            "description_en": "Tasnif (EN)",
            "description_ko": "Tasnif (KO)",
        }
        required = {
            "title_uz": True,
            "title_ru": True,
            "title_en": True,
            "title_ko": True,
        }

    start_date = forms.DateTimeField(
        input_formats=["%Y-%m-%d"],  # Adjust the format as needed
        widget=forms.DateTimeInput(attrs={"type": "date", "class": "form-control"}),
        label="Boshlanish sanasi",
    )
    end_date = forms.DateTimeField(
        input_formats=["%Y-%m-%d"],  # Adjust the format as needed
        widget=forms.DateTimeInput(attrs={"type": "date", "class": "form-control"}),
        label="Tugash sanasi",
    )

    def save(self, commit=True):
        news = super(NewsForm, self).save(commit=False)

        new_image = self.cleaned_data.get("image", None)
        if new_image:
            # If the new image is an instance of InMemoryUploadedFile, use its content directly
            if isinstance(new_image, InMemoryUploadedFile):
                news.image.save(new_image.name, new_image)
        if commit:
            news.save()
        return news


class NewsEditForm(forms.ModelForm):
    start_date = forms.DateTimeField(
        input_formats=["%Y-%m-%d"],  # Adjust the format as needed
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"}
        ),
        initial=timezone.now(),
        label="Boshlanish sanasi",
    )

    end_date = forms.DateTimeField(
        input_formats=["%Y-%m-%d"],  # Adjust the format as needed
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"}
        ),
        initial=timezone.now(),
        label="Tugash sanasi",
    )
    description_uz = forms.CharField(
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
        label="Ta`rif UZ",
        required=True,
    )

    description_ru = forms.CharField(
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
        label="Ta`rif RU",
        required=True,
    )

    description_en = forms.CharField(
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
        label="Ta`rif EN",
        required=True,
    )

    description_ko = forms.CharField(
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
        label="Ta`rif KO",
        required=True,
    )

    class Meta:
        model = News
        fields = [
            "title_uz",
            "title_ru",
            "title_en",
            "title_ko",
            "image",
            "start_date",
            "end_date",
            "description_uz",
            "description_ru",
            "description_en",
            "description_ko",
            "active",
        ]

        widgets = {
            "title_uz": forms.TextInput(attrs={"class": "form-control"}),
            "title_ru": forms.TextInput(attrs={"class": "form-control"}),
            "title_en": forms.TextInput(attrs={"class": "form-control"}),
            "title_ko": forms.TextInput(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "description_uz": forms.Textarea(attrs={"class": "form-control"}),
            "description_ru": forms.Textarea(attrs={"class": "form-control"}),
            "description_en": forms.Textarea(attrs={"class": "form-control"}),
            "description_ko": forms.Textarea(attrs={"class": "form-control"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

        labels = {
            "title_uz": "Sarlovha (UZ)",
            "title_ru": "Sarlovha (RU)",
            "title_en": "Sarlovha (EN)",
            "title_ko": "Sarlovha (KO)",
            "description_uz": "Tasnif (UZ)",
            "description_ru": "Tasnif (RU)",
            "description_en": "Tasnif (EN)",
            "description_ko": "Tasnif (KO)",
        }

        required = {
            "title_uz": True,
            "title_ru": True,
            "title_en": True,
            "title_ko": True,
            "description_uz": True,
            "description_ru": True,
            "description_en": True,
            "description_ko": True,
        }

    def save(self, commit=False):
        news = super().save(commit=False)
        if not news.start_date:
            news.start_date = self.cleaned_data["start_date"]
        if not news.end_date:
            news.end_date = self.cleaned_data["end_date"]
        new_image = self.cleaned_data.get("image", None)
        if new_image:
            # If the new image is an instance of InMemoryUploadedFile, use its content directly
            if isinstance(new_image, InMemoryUploadedFile):
                news.image.save(new_image.name, new_image)
        if commit:
            news.save()

        return news


class ServiceEditForm(forms.ModelForm):
    delivery_fee = forms.DecimalField(
        decimal_places=0,
        max_digits=10,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        label="Yetkazib berish xizmati narxi",
    )

    class Meta:
        model = Service
        fields = [
            "delivery_fee",
        ]

    def __init__(self, *args, **kwargs):
        super(ServiceEditForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields["delivery_fee"].initial = self.instance.delivery_fee

    def save(self, commit=True):
        service = super(ServiceEditForm, self).save(commit=False)
        if commit:
            service.save()
        return service


class ReminderForm(forms.ModelForm):
    class Meta:
        model = Information
        fields = [
            "reminder_uz",
            "reminder_ru",
            "reminder_en",
            "reminder_ko",
        ]

    reminder_uz = forms.CharField(
        required=False,
        label="Eslatma UZ",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    reminder_ru = forms.CharField(
        required=False,
        label="Eslatma RU",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    reminder_en = forms.CharField(
        required=False,
        label="Eslatma EN",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    reminder_ko = forms.CharField(
        required=False,
        label="Eslatma KO",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )


class AgrementForm(forms.ModelForm):
    agreement_uz = forms.CharField(
        required=False,
        label="Kelishuv UZ",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    agreement_ru = forms.CharField(
        required=False,
        label="Kelishuv RU",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    agreement_en = forms.CharField(
        required=False,
        label="Kelishuv EN",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    agreement_ko = forms.CharField(
        required=False,
        label="Kelishuv KO",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )

    class Meta:
        model = Information
        fields = [
            "agreement_uz",
            "agreement_ru",
            "agreement_en",
            "agreement_ko",
        ]


class ShipmentForm(forms.ModelForm):
    shipment_terms_uz = forms.CharField(
        required=False,
        label="Yetkazish shartlari UZ",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    shipment_terms_ru = forms.CharField(
        required=False,
        label="Yetkazish shartlari RU",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    shipment_terms_en = forms.CharField(
        required=False,
        label="Yetkazish shartlari EN",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    shipment_terms_ko = forms.CharField(
        required=False,
        label="Yetkazish shartlari KO",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )

    class Meta:
        model = Information
        fields = [
            "shipment_terms_uz",
            "shipment_terms_ru",
            "shipment_terms_en",
            "shipment_terms_ko",
        ]


class PrivacyForm(forms.ModelForm):
    privacy_policy_uz = forms.CharField(
        required=False,
        label="Offerta shartlari UZ",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    privacy_policy_ru = forms.CharField(
        required=False,
        label="Offerta shartlari RU",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    privacy_policy_en = forms.CharField(
        required=False,
        label="Offerta shartlari EN",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    privacy_policy_ko = forms.CharField(
        required=False,
        label="Offerta shartlari KO",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )

    class Meta:
        model = Information
        fields = [
            "privacy_policy_uz",
            "privacy_policy_ru",
            "privacy_policy_en",
            "privacy_policy_ko",
        ]


class AboutUsForm(forms.ModelForm):
    about_us_uz = forms.CharField(
        required=False,
        label="Biz haqimizda UZ",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    about_us_ru = forms.CharField(
        required=False,
        label="Biz haqimizda RU",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    about_us_en = forms.CharField(
        required=False,
        label="Biz haqimizda EN",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    about_us_ko = forms.CharField(
        required=False,
        label="Biz haqimizda KO",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )

    class Meta:
        model = Information
        fields = [
            "about_us_uz",
            "about_us_ru",
            "about_us_en",
            "about_us_ko",
        ]


class SupportForm(forms.ModelForm):
    support_center_uz = forms.CharField(
        required=False,
        label="Qollab quvvatlash markazi UZ",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    support_center_ru = forms.CharField(
        required=False,
        label="Qollab quvvatlash markazi RU",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    support_center_en = forms.CharField(
        required=False,
        label="Qollab quvvatlash markazi EN",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    support_center_ko = forms.CharField(
        required=False,
        label="Qollab quvvatlash markazi KO",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )

    class Meta:
        model = Information
        fields = [
            "support_center_uz",
            "support_center_ru",
            "support_center_en",
            "support_center_ko",
        ]


class PaymentForm(forms.ModelForm):
    payment_data_uz = forms.CharField(
        required=False,
        label="Hisob raqam/Pul o'tkazish shartlari UZ",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    payment_data_ru = forms.CharField(
        required=False,
        label="Hisob raqam/Pul o'tkazish shartlari RU",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    payment_data_en = forms.CharField(
        required=False,
        label="Hisob raqam/Pul o'tkazish shartlari EN",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    payment_data_ko = forms.CharField(
        required=False,
        label="Hisob raqam/Pul o'tkazish shartlari KO",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )

    class Meta:
        model = Information
        fields = [
            "payment_data_uz",
            "payment_data_ru",
            "payment_data_en",
            "payment_data_ko",
        ]


class InformationEditForm(forms.ModelForm):
    reminder_uz = forms.CharField(
        required=False,
        label="Eslatma UZ",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    reminder_ru = forms.CharField(
        required=False,
        label="Eslatma RU",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    reminder_en = forms.CharField(
        required=False,
        label="Eslatma EN",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    reminder_ko = forms.CharField(
        required=False,
        label="Eslatma KR",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    agreement_uz = forms.CharField(
        required=False,
        label="Kelishuv UZ",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    agreement_ru = forms.CharField(
        required=False,
        label="Kelishuv RU",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    agreement_en = forms.CharField(
        required=False,
        label="Kelishuv EN",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    agreement_ko = forms.CharField(
        required=False,
        label="Kelishuv KR",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    shipment_terms_uz = forms.CharField(
        required=False,
        label="Yetkazish shartlari UZ",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    shipment_terms_ru = forms.CharField(
        required=False,
        label="Yetkazish shartlari RU",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    shipment_terms_en = forms.CharField(
        required=False,
        label="Yetkazish shartlari EN",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    shipment_terms_ko = forms.CharField(
        required=False,
        label="Yetkazish shartlari KR",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    privacy_policy_uz = forms.CharField(
        required=False,
        label="Offerta shartlari UZ",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    privacy_policy_ru = forms.CharField(
        required=False,
        label="Offerta shartlari RU",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    privacy_policy_en = forms.CharField(
        required=False,
        label="Offerta shartlari EN",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    privacy_policy_ko = forms.CharField(
        required=False,
        label="Offerta shartlari KR",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    about_us_uz = forms.CharField(
        required=False,
        label="Biz haqimizda UZ",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    about_us_ru = forms.CharField(
        required=False,
        label="Biz haqimizda RU",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    about_us_en = forms.CharField(
        required=False,
        label="Biz haqimizda EN",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    about_us_ko = forms.CharField(
        required=False,
        label="Biz haqimizda KR",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    support_center_uz = forms.CharField(
        required=False,
        label="Qollab quvvatlash markazi UZ",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    support_center_ru = forms.CharField(
        required=False,
        label="Qollab quvvatlash markazi RU",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    support_center_en = forms.CharField(
        required=False,
        label="Qollab quvvatlash markazi EN",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    support_center_ko = forms.CharField(
        required=False,
        label="Qollab quvvatlash markazi KR",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    payment_data_uz = forms.CharField(
        required=False,
        label="Hisob raqam/Pul o'tkazish shartlari UZ",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    payment_data_ru = forms.CharField(
        required=False,
        label="Hisob raqam/Pul o'tkazish shartlari RU",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    payment_data_en = forms.CharField(
        required=False,
        label="Hisob raqam/Pul o'tkazish shartlari EN",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )
    payment_data_ko = forms.CharField(
        required=False,
        label="Hisob raqam/Pul o'tkazish shartlari KR",
        widget=CKEditorWidget(
            attrs={"class": "form-control ckeditor", "rows": 10, "cols": 100}
        ),
    )

    class Meta:
        model = Information
        fields = [
            "reminder_uz",
            "reminder_ru",
            "reminder_en",
            "reminder_ko",
            "agreement_uz",
            "agreement_ru",
            "agreement_en",
            "agreement_ko",
            "shipment_terms_uz",
            "shipment_terms_ru",
            "shipment_terms_en",
            "shipment_terms_ko",
            "privacy_policy_uz",
            "privacy_policy_ru",
            "privacy_policy_en",
            "privacy_policy_ko",
            "about_us_uz",
            "about_us_ru",
            "about_us_en",
            "about_us_ko",
            "support_center_uz",
            "support_center_ru",
            "support_center_en",
            "support_center_ko",
            "payment_data_uz",
            "payment_data_ru",
            "payment_data_en",
            "payment_data_ko",
        ]

    def __init__(self, *args, **kwargs):
        super(InformationEditForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields["reminder_uz"].initial = self.instance.reminder_uz
            self.fields["reminder_ru"].initial = self.instance.reminder_ru
            self.fields["reminder_en"].initial = self.instance.reminder_en
            self.fields["reminder_ko"].initial = self.instance.reminder_ko
            self.fields["agreement_uz"].initial = self.instance.agreement_uz
            self.fields["agreement_ru"].initial = self.instance.agreement_ru
            self.fields["agreement_en"].initial = self.instance.agreement_en
            self.fields["agreement_ko"].initial = self.instance.agreement_ko
            self.fields["shipment_terms_uz"].initial = self.instance.shipment_terms_uz
            self.fields["shipment_terms_ru"].initial = self.instance.shipment_terms_ru
            self.fields["shipment_terms_en"].initial = self.instance.shipment_terms_en
            self.fields["shipment_terms_ko"].initial = self.instance.shipment_terms_ko
            self.fields["privacy_policy_uz"].initial = self.instance.privacy_policy_uz
            self.fields["privacy_policy_ru"].initial = self.instance.privacy_policy_ru
            self.fields["privacy_policy_en"].initial = self.instance.privacy_policy_en
            self.fields["privacy_policy_ko"].initial = self.instance.privacy_policy_ko
            self.fields["about_us_uz"].initial = self.instance.about_us_uz
            self.fields["about_us_ru"].initial = self.instance.about_us_ru
            self.fields["about_us_en"].initial = self.instance.about_us_en
            self.fields["about_us_ko"].initial = self.instance.about_us_ko
            self.fields["support_center_uz"].initial = self.instance.support_center_uz
            self.fields["support_center_ru"].initial = self.instance.support_center_ru
            self.fields["support_center_en"].initial = self.instance.support_center_en
            self.fields["support_center_ko"].initial = self.instance.support_center_ko
            self.fields["payment_data_uz"].initial = self.instance.payment_data_uz
            self.fields["payment_data_ru"].initial = self.instance.payment_data_ru
            self.fields["payment_data_en"].initial = self.instance.payment_data_en
            self.fields["payment_data_ko"].initial = self.instance.payment_data_ko

    def clean(self):
        cleaned_data = super().clean()
        initial_values = {}

        for field_name in self.fields:
            initial_values[field_name] = getattr(self.instance, field_name)

        for field_name, initial_value in initial_values.items():
            new_value = cleaned_data.get(field_name)
            if new_value == initial_value:
                cleaned_data[field_name] = initial_value

        return cleaned_data

    def save(self, commit=True):
        information = super().save(commit=False)
        changed_fields = []

        # Compare cleaned data with initial values
        for field_name, field_value in self.cleaned_data.items():
            if field_value != getattr(information, field_name):
                changed_fields.append(field_name)

        # Set unchanged fields to their initial values
        for field_name in set(self.fields) - set(changed_fields):
            setattr(information, field_name, getattr(self.instance, field_name))

        if commit:
            information.save()

        return information


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ["title", "image", "active"]

        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "title": "Sarlavhasi",
            "image": "Rasmi",
        }


class CategoryEditForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            "main_type",
            "name_uz",
            "name_ru",
            "name_en",
            "name_ko",
            "image",
            "active",
        ]
        widgets = {
            "main_type": forms.Select(attrs={"class": "form-control"}),
            "name_uz": forms.TextInput(attrs={"class": "form-control"}),
            "name_ru": forms.TextInput(attrs={"class": "form-control"}),
            "name_en": forms.TextInput(attrs={"class": "form-control"}),
            "name_ko": forms.TextInput(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "name_uz": "Nomi (UZ)",
            "name_ru": "Nomi (RU)",
            "name_en": "Nomi (EN)",
            "name_ko": "Nomi (KR)",
            "main_type": "Qaysi turga mansubligi",
        }

    def __init__(self, *args, **kwargs):
        super(CategoryEditForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields["main_type"].initial = self.instance.main_type
            self.fields["name_uz"].initial = self.instance.name_uz
            self.fields["name_ru"].initial = self.instance.name_ru
            self.fields["name_en"].initial = self.instance.name_en
            self.fields["name_ko"].initial = self.instance.name_ko
            self.fields["image"].initial = self.instance.image
            self.fields["active"].initial = self.instance.active




class CategoryCreateForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = [
            "main_type",
            "name_uz",
            "name_ru",
            "name_en",
            "name_ko",
            "image",
            "active",
        ]
        widgets = {
            "main_type": forms.Select(attrs={"class": "form-control"}),
            "name_uz": forms.TextInput(attrs={"class": "form-control"}),
            "name_ru": forms.TextInput(attrs={"class": "form-control"}),
            "name_en": forms.TextInput(attrs={"class": "form-control"}),
            "name_ko": forms.TextInput(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "name_uz": "Nomi (UZ)",
            "name_ru": "Nomi (RU)",
            "name_en": "Nomi (EN)",
            "name_ko": "Nomi (KR)",
            "main_type": "Qaysi turga mansubligi",
        }
        required = {
            "name_uz": True,
            "name_ru": True,
            "name_en": True,
            "name_ko": True,
        }

    def __init__(self, *args, **kwargs):
        super(CategoryCreateForm, self).__init__(*args, **kwargs)

        # Set required attribute for each field
        self.fields["name_uz"].required = True
        self.fields["name_ru"].required = True
        self.fields["name_en"].required = True
        self.fields["name_ko"].required = True
        self.fields["main_type"].required = True

    def save(self, commit=True):
        instance = super(CategoryCreateForm, self).save(commit=False)
        if commit:
            instance.save()
        return instance




class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class BonusEditForm(forms.ModelForm):
    title = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}), label="Toifasi"
    )
    amount = forms.DecimalField(
        decimal_places=0,
        max_digits=10,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        label="Buyurtma qiymati",
    )
    percentage = forms.IntegerField(
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        label="Chegirma foizi qiymati",
    )
    active = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        required=False,
        initial=True,
    )

    class Meta:
        model = Bonus
        fields = ["title", "amount", "percentage", "active"]

    def __init__(self, *args, **kwargs):
        super(BonusEditForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields["title"].initial = self.instance.title
            self.fields["amount"].initial = self.instance.amount
            self.fields["percentage"].initial = self.instance.percentage
            self.fields["active"].initial = self.instance.active

    def save(self, commit=True):
        bonus = super(BonusEditForm, self).save(commit=False)
        if commit:
            bonus.save()
        return bonus


class SocialMediaEditForm(forms.ModelForm):
    telegram = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Telegram",
        required=False,
    )
    instagram = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Instagram",
        required=False,
    )
    whatsapp = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Whatsapp",
        required=False,
    )
    phone_number = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Telefon nomer",
        required=False,
    )
    imo = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="IMO",
        required=False,
    )
    kakao = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Kakao talk",
        required=False,
    )
    tiktok = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="TikTok",
        required=False,
    )

    class Meta:
        model = SocialMedia
        fields = [
            "telegram",
            "instagram",
            "whatsapp",
            "phone_number",
            "imo",
            "kakao",
            "tiktok",
        ]

    def clean(self):
        cleaned_data = super().clean()

        for field_name in ["telegram", "instagram", "whatsapp", "tiktok"]:
            if cleaned_data.get(field_name) and cleaned_data[field_name] != getattr(
                self.instance, field_name
            ):
                original_value = getattr(self.instance, field_name)
                cleaned_data[field_name] = self.get_cleaned_url(
                    field_name, cleaned_data[field_name], original_value
                )

        return cleaned_data

    def get_cleaned_url(self, field_name, value, original_value):
        if any(
            original_value.startswith(prefix)
            for prefix in [
                f"https://www.tiktok.com/@{value}",
                f"https://www.{field_name}.com/",
                "https://t.me/",
                "https://wa.me/",
            ]
        ):
            return value  # Don't add the prefix again
        else:
            # Add the prefix based on the social media platform
            if field_name == "telegram":
                return f"https://t.me/{value}"
            elif field_name == "instagram":
                return f"https://www.instagram.com/{value}"
            elif field_name == "whatsapp":
                return f"https://wa.me/{value}"
            elif field_name == "tiktok":
                return f"https://www.tiktok.com/@{value}"
            else:
                return value

    def __init__(self, *args, **kwargs):
        super(SocialMediaEditForm, self).__init__(*args, **kwargs)
        if self.instance:
            for field_name in [
                "telegram",
                "instagram",
                "whatsapp",
                "phone_number",
                "imo",
                "kakao",
                "tiktok",
            ]:
                self.fields[field_name].initial = getattr(self.instance, field_name)

    def save(self, commit=True):
        media = super(SocialMediaEditForm, self).save(commit=commit)
        return media



class PhoneCategoryCreateForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"
        exclude = ["main_type"]
        widgets = {
            # 'main_type': forms.Select(attrs={'class': 'form-control'}),
            "name_uz": forms.TextInput(attrs={"class": "form-control"}),
            "name_ru": forms.TextInput(attrs={"class": "form-control"}),
            "name_en": forms.TextInput(attrs={"class": "form-control"}),
            "name_ko": forms.TextInput(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "name_uz": "Nomi (UZ)",
            "name_ru": "Nomi (RU)",
            "name_en": "Nomi (EN)",
            "name_ko": "Nomi (KR)",
        }
        required = {
            "name_uz": True,
            "name_ru": True,
            "name_en": True,
            "name_ko": True,
        }

    def __init__(self, *args, **kwargs):
        super(PhoneCategoryCreateForm, self).__init__(*args, **kwargs)

        # Set required attribute for each field
        self.fields["name_uz"].required = True
        self.fields["name_ru"].required = True
        self.fields["name_en"].required = True
        self.fields["name_ko"].required = True




class TicketCategoryCreateForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name_uz", "name_ru", "name_en", "name_ko", "image", "desc", "active"]
        widgets = {
            "name_uz": forms.TextInput(attrs={"class": "form-control"}),
            "name_ru": forms.TextInput(attrs={"class": "form-control"}),
            "name_en": forms.TextInput(attrs={"class": "form-control"}),
            "name_ko": forms.TextInput(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "name_uz": "Nomi (UZ)",
            "name_ru": "Nomi (RU)",
            "name_en": "Nomi (EN)",
            "name_ko": "Nomi (KR)",
            "image": "Rasm",
        }
        required = {
            "name_uz": True,
            "name_ru": True,
            "name_en": True,
            "name_ko": True,
        }

    def __init__(self, *args, **kwargs):
        super(TicketCategoryCreateForm, self).__init__(*args, **kwargs)

        # Set required attribute for each field
        self.fields["name_uz"].required = True
        self.fields["name_ru"].required = True
        self.fields["name_en"].required = True
        self.fields["name_ko"].required = True



class PhoneEditForm(forms.ModelForm):
    product_desc_uz = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control"}),
        label="Ta`rif UZ",
    )
    product_desc_ru = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control"}),
        label="Ta`rif RU",
    )
    product_desc_en = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control"}),
        label="Ta`rif EN",
    )
    product_desc_ko = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control"}),
        label="Ta`rif KR",
    )
    product_old_price = forms.DecimalField(
        decimal_places=0,
        max_digits=10,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        label="Maxsulot narxi",
    )
    product_new_price = forms.DecimalField(
        decimal_places=0,
        max_digits=10,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        label="Chegirmadagi narxi",
    )
    weight = forms.DecimalField(
        decimal_places=1,
        max_digits=10,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        label="Maxsulot og`irligi (KG)",
        initial=1,
    )
    product_available_quantity = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        label="Mavjud miqdori",
    )
    images = MultipleFileField(required=False)
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(main_type="p"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Kategoriyasi",
    )
    product_active = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    class Meta:
        model = Phone
        fields = [
            "model_name",
            "color",
            "condition",
            "ram",
            "storage",
            "category",
            "images",
            "product_old_price",
            "product_new_price",
            "product_available_quantity",
            "weight",
            "product_desc_uz",
            "product_desc_ru",
            "product_desc_en",
            "product_desc_ko",
            "product_active",
        ]
        widgets = {
            "model_name": forms.TextInput(attrs={"class": "form-control"}),
            "color": forms.Select(attrs={"class": "form-select"}),
            "condition": forms.Select(attrs={"class": "form-select"}),
            "ram": forms.Select(attrs={"class": "form-select"}),
            "storage": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "images": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "model_name": "Model nomi",
            "ram": "Operativ xotirasi (RAM)",
            "storage": "Ichki xotirasi",
            "color": "Rangi",
            "condition": "Holati",
            "category": "Kategoriyasi",
            "images": "Ramslar",
        }

    def __init__(self, *args, **kwargs):
        super(PhoneEditForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.product:
            product = self.instance.product
            self.fields["weight"].initial = product.weight
            self.fields["product_old_price"].initial = product.old_price
            self.fields["product_new_price"].initial = product.new_price
            self.fields["product_available_quantity"].initial = (
                product.available_quantity
            )
            self.fields["product_desc_uz"].initial = product.desc_uz
            self.fields["product_desc_ru"].initial = product.desc_ru
            self.fields["product_desc_en"].initial = product.desc_en
            self.fields["product_desc_ko"].initial = product.desc_ko
            self.fields["product_active"].initial = product.active

    def save(self, commit=True):
        phone = super(PhoneEditForm, self).save(commit=False)
        if not phone.product_id:
            phone.product = ProductItem()
        get_weight = self.cleaned_data.get("weight", None)
        product_item = phone.product
        product_item.old_price = self.cleaned_data["product_old_price"]
        product_item.new_price = self.cleaned_data["product_new_price"]
        product_item.weight = get_weight if get_weight else 1
        product_item.available_quantity = self.cleaned_data[
            "product_available_quantity"
        ]
        product_item.desc_uz = self.cleaned_data["product_desc_uz"]
        product_item.desc_ru = self.cleaned_data["product_desc_ru"]
        product_item.desc_en = self.cleaned_data["product_desc_en"]
        product_item.desc_ko = self.cleaned_data["product_desc_ko"]
        product_item.active = self.cleaned_data["product_active"]
        if commit:
            product_item.save()
            phone.product = product_item
            phone.category = self.cleaned_data["category"]
            phone.save()
            existing_images = phone.product.images.all()
            form_images = self.files.getlist("images")
            if form_images:
                for existing_image in existing_images:
                    if existing_image.image.name not in form_images:
                        existing_image.delete()
                for img in form_images:
                    image = Image(
                        image=img,
                        name=f"{self.cleaned_data['model_name']}_{img.name}",
                        product=product_item,
                    )
                    image.save()
        return phone




class GoodCategoryCreateForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(main_type="f"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Kategoriyasi",
    )

    class Meta:
        model = Category
        fields = [
            "name_uz",
            "name_ru",
            "name_en",
            "name_ko",
            "image",
            "category",
            "active",
        ]
        widgets = {
            "name_uz": forms.TextInput(attrs={"class": "form-control"}),
            "name_ru": forms.TextInput(attrs={"class": "form-control"}),
            "name_en": forms.TextInput(attrs={"class": "form-control"}),
            "name_ko": forms.TextInput(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "name_uz": "Nomi (UZ)",
            "name_ru": "Nomi (RU)",
            "name_en": "Nomi (EN)",
            "name_ko": "Nomi (KR)",
            "category": "Kategoriyasi",
            "image": "Rasmi",
        }
        required = {
            "name_uz": True,
            "name_ru": True,
            "name_en": True,
            "name_ko": True,
        }

    def __init__(self, *args, **kwargs):
        super(GoodCategoryCreateForm, self).__init__(*args, **kwargs)

        # Set required attribute for each field
        self.fields["name_uz"].required = True
        self.fields["name_ru"].required = True
        self.fields["name_en"].required = True
        self.fields["name_ko"].required = True

    def save(self, commit=True):
        instance = super(GoodCategoryCreateForm, self).save(commit=False)
        instance.main_type = "f"

        if commit:
            instance.save()
        return instance




class TicketEditForm(forms.ModelForm):
    product_desc_uz = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control"}),
        label="Ta`rif UZ",
    )
    product_desc_ru = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control"}),
        label="Ta`rif RU",
    )
    product_desc_en = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control"}),
        label="Ta`rif EN",
    )
    product_desc_ko = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control"}),
        label="Ta`rif KR",
    )
    product_new_price = forms.DecimalField(
        decimal_places=0,
        max_digits=10,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        label="Chegirmadagi narxi",
    )
    product_old_price = forms.DecimalField(
        decimal_places=0,
        max_digits=10,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        label="Maxsulot narxi",
    )
    weight = forms.DecimalField(
        decimal_places=1,
        max_digits=10,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        label="Maxsulot og`irligi (KG)",
        required=False,
        initial=1,
    )
    images = MultipleFileField(required=False)
    product_available_quantity = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        label="Mavjud miqdori",
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(main_type="t"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Kategoriyasi",
    )
    product_active = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    class Meta:
        model = Ticket
        exclude = ["event_date"]
        fields = [
            "event_name_uz",
            "event_name_ru",
            "event_name_en",
            "event_name_ko",
            "event_date",
            "category",
            "images",
            "product_old_price",
            "product_new_price",
            "product_available_quantity",
            "weight",
            "product_desc_uz",
            "product_desc_ru",
            "product_desc_en",
            "product_desc_ko",
            "product_active",
        ]
        widgets = {
            "event_name_uz": forms.TextInput(attrs={"class": "form-control"}),
            "event_name_en": forms.TextInput(attrs={"class": "form-control"}),
            "event_name_ru": forms.TextInput(attrs={"class": "form-control"}),
            "event_name_ko": forms.TextInput(attrs={"class": "form-control"}),
            "event_date": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "product_desc_uz": forms.TextInput(attrs={"class": "form-control"}),
            "product_desc_ru": forms.TextInput(attrs={"class": "form-control"}),
            "product_desc_en": forms.TextInput(attrs={"class": "form-control"}),
            "product_desc_ko": forms.TextInput(attrs={"class": "form-control"}),
            "images": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "event_name_uz": "Sarlavha (UZ)",
            "event_name_en": "Sarlavha (EN)",
            "event_name_ru": "Sarlavha (RU)",
            "event_name_ko": "Sarlavha (KR)",
            "event_date": "Hodisa sanasi",
            "category": "Kategoriyasi",
            "product_desc_uz": "Ta`rif (UZ)",
            "product_desc_ru": "Ta`rif (RU)",
            "product_desc_en": "Ta`rif (EN)",
            "product_desc_ko": "Ta`rif (KR)",
            "images": "Rasmlar",
        }

    def __init__(self, *args, **kwargs):
        super(TicketEditForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.product:
            product = self.instance.product
            self.fields["weight"].initial = product.weight
            self.fields["product_desc_uz"].initial = product.desc_uz
            self.fields["product_desc_ru"].initial = product.desc_ru
            self.fields["product_desc_en"].initial = product.desc_en
            self.fields["product_desc_ko"].initial = product.desc_ko
            self.fields["product_old_price"].initial = product.old_price
            self.fields["product_new_price"].initial = product.new_price
            self.fields["product_available_quantity"].initial = (
                product.available_quantity
            )
            self.fields["product_active"].initial = product.active

    def save(self, commit=True):
        ticket = super(TicketEditForm, self).save(commit=False)

        if not ticket.product_id:
            ticket.product = ProductItem()
        product_item = ticket.product
        get_weight = self.cleaned_data.get("weight", None)
        product_item.weight = get_weight if get_weight else 1
        product_item.desc_uz = self.cleaned_data["product_desc_uz"]
        product_item.desc_ru = self.cleaned_data["product_desc_ru"]
        product_item.desc_en = self.cleaned_data["product_desc_en"]
        product_item.desc_ko = self.cleaned_data["product_desc_ko"]
        product_item.new_price = self.cleaned_data["product_old_price"]
        product_item.new_price = self.cleaned_data["product_new_price"]
        product_item.available_quantity = self.cleaned_data[
            "product_available_quantity"
        ]
        product_item.active = self.cleaned_data["product_active"]

        if commit:
            product_item.save()
            ticket.product = product_item
            ticket.category = self.cleaned_data["category"]
            ticket.save()
            existing_images = ticket.product.images.all()
            form_images = self.files.getlist("images")
            if form_images:
                for existing_image in existing_images:
                    if existing_image.image.name not in form_images:
                        existing_image.delete()
                for img in form_images:
                    image = Image(
                        image=img,
                        name=f"{self.cleaned_data['event_name_uz']}_{img.name}",
                        product=product_item,
                    )
                    image.save()

        return ticket



class GoodMainCategoryCreateForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name_uz", "name_ru", "name_en", "name_ko", "image", "active"]
        widgets = {
            "name_uz": forms.TextInput(attrs={"class": "form-control"}),
            "name_ru": forms.TextInput(attrs={"class": "form-control"}),
            "name_en": forms.TextInput(attrs={"class": "form-control"}),
            "name_ko": forms.TextInput(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            # "stock": forms.NumberInput(attrs={"class": "form-control"}),
            # "bonus": forms.NumberInput(attrs={"class": "form-control"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "name_uz": "Nomi (UZ)",
            "name_ru": "Nomi (RU)",
            "name_en": "Nomi (EN)",
            "name_ko": "Nomi (KR)",
        }
        required = {
            "name_uz": True,
            "name_ru": True,
            "name_en": True,
            "name_ko": True,
        }

    def __init__(self, *args, **kwargs):
        super(GoodMainCategoryCreateForm, self).__init__(*args, **kwargs)

        # Set required attribute for each field
        self.fields["name_uz"].required = True
        self.fields["name_ru"].required = True
        self.fields["name_en"].required = True
        self.fields["name_ko"].required = True

        # Filter the category queryset to main_type='f'
        if "category" in self.fields:
            self.fields["category"].queryset = Category.objects.filter(main_type="f")

    def save(self, commit=True):
        # Save the category with main_type='f'
        instance = super(GoodMainCategoryCreateForm, self).save(commit=False)
        instance.main_type = "f"
        if commit:
            instance.save()
        return instance




class GoodChildProductItemForm(forms.ModelForm):
    def __init__(self, *args, product_type=None, **kwargs):
        self.product_type = product_type
        super().__init__(*args, **kwargs)

    class Meta:
        model = Good
        fields = [
            "name_ko",
            "name_uz",
            "name_en",
            "name_ru",
        ]

    name_en = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Nomi (EN)",
    )
    name_ko = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Nomi (KR)",
    )
    name_uz = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Nomi (UZ)",
    )
    name_ru = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Nomi (RU)",
    )

    available_quantity = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        label="Mavjud miqdori",
    )
    active = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        initial=True,
        required=False,
    )

    images = (
        MultipleFileField()
    )  # New field for multiple images # New field for multiple images

    def save(self, commit=True):
        good = super().save(commit=False)
        good.name_en = self.cleaned_data.get("name_en")
        good.name_uz = self.cleaned_data.get("name_uz")
        good.name_ru = self.cleaned_data.get("name_ru")
        good.name_ko = self.cleaned_data.get("name_ko")

        if self.product_type is None:
            raise ValueError("product_type must be provided")
        parent = Good.objects.get(product__product_type=self.product_type, product__main=True)
        product_item = ProductItem(
            available_quantity=self.cleaned_data["available_quantity"],
            active=self.cleaned_data["active"],
            product_type=self.product_type,
            main=False,
            new_price=parent.product.new_price,
            old_price=parent.product.old_price,
            desc_uz=parent.product.desc_uz,
            desc_ru=parent.product.desc_ru,
            desc_en=parent.product.desc_en,
            desc_ko=parent.product.desc_ko,
            measure=parent.product.measure,
            weight=parent.product.weight,

            # Ensure this is set
        )

        if commit:

            product_item.save()
            good.product = product_item
            good.sub_cat = parent.sub_cat
            good.save()

            # Save multiple images
            for img in self.files.getlist("images"):
                image = Image(
                    image=img,
                    name=f"{self.cleaned_data['name_uz']}_{img.name}",
                    product=product_item,
                )
                image.save()
        return good
