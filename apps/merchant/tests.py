from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.customer.models import Profile
from apps.merchant.models import Order, OrderItem
from apps.product.models import ProductItem


class CartDeleteBehaviorTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user_model = get_user_model()

		self.user = self.user_model.objects.create_user(
			username="998901112233",
			password="testpass123",
		)
		self.profile = Profile.objects.create(
			origin=self.user,
			full_name="Test User",
			phone_number="998901112233",
		)

		self.product_1 = ProductItem.objects.create(
			desc="Test product 1",
			old_price=1000,
			new_price=900,
			available_quantity=100,
		)
		self.product_2 = ProductItem.objects.create(
			desc="Test product 2",
			old_price=2000,
			new_price=0,
			available_quantity=100,
		)

		self.order = Order.objects.create(user=self.profile, status="in_cart")
		self.item_1 = OrderItem.objects.create(order=self.order, product=self.product_1, quantity=2)
		self.item_2 = OrderItem.objects.create(order=self.order, product=self.product_2, quantity=1)

		self.client.force_authenticate(user=self.user)

	def test_order_delete_with_orderitem_id_deletes_only_one_item(self):
		url = f"/api/merchant/order/{self.item_1.id}/retriev/"

		response = self.client.delete(url)
		self.assertEqual(response.status_code, 204)

		self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())
		self.assertFalse(OrderItem.objects.filter(pk=self.item_1.pk).exists())
		self.assertTrue(OrderItem.objects.filter(pk=self.item_2.pk).exists())

	def test_in_cart_order_delete_does_not_delete_order(self):
		url = f"/api/merchant/order/{self.order.id}/retriev/"

		response = self.client.delete(url)
		self.assertIn(response.status_code, (204, 400))

		# Muhimi: savat orderi o'chib ketmasin (aks holda hamma itemlar CASCADE bo'lib ketadi)
		self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())

		# Savat to'liq tozalanib ketmasin
		remaining_items = OrderItem.objects.filter(order=self.order).count()
		self.assertGreaterEqual(remaining_items, 1)

	def test_non_cart_order_delete_still_works(self):
		non_cart_order = Order.objects.create(user=self.profile, status="pending")
		OrderItem.objects.create(order=non_cart_order, product=self.product_1, quantity=1)

		url = f"/api/merchant/order/{non_cart_order.id}/retriev/"
		response = self.client.delete(url)

		self.assertEqual(response.status_code, 204)
		self.assertFalse(Order.objects.filter(pk=non_cart_order.pk).exists())
