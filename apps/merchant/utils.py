from django.db.models import Sum, F
from .models import Order, OrderItem
from apps.product.models import ProductItem


def reduce_product_stock():
    sent_order_items = OrderItem.objects.filter(order__status="sent")

    product_quantities = sent_order_items.values("product").annotate(
        total_quantity=Sum("quantity")
    )

    for item in product_quantities:
        product_id = item["product"]
        total_quantity = item["total_quantity"]

        product = ProductItem.objects.get(id=product_id)
        product.available_quantity = F("available_quantity") - total_quantity
        product.save()
