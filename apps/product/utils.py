from rest_framework import serializers

from .models import ProductItem


class ProductItemCreatorMixin(serializers.ModelSerializer):
    def create_pruduct(self, validation_data):
        product_item = validation_data.pop("product")
        product = ProductItem.objects.create(**product_item)
        return product