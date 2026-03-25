from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.models import User
from orders.models import Category, Good, Order, OrderGood, PromoCode
from orders.services.orders import OrderService


class OrderServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.category = Category.objects.create(name="Electronics")
        self.good = Good.objects.create(
            name="Phone", category=self.category, quantity=10, price=Decimal("100.00")
        )
        now = timezone.now()
        self.promo = PromoCode.objects.create(
            code="TEST10",
            discount_percent=Decimal("0.10"),
            max_uses_count=100,
            started_at=now - timedelta(days=1),
            finished_at=now + timedelta(days=1),
        )

    def test_create_order_success(self):
        """Тест успешного создания заказа"""
        goods_data = [{"good_id": self.good.id, "quantity": 2}]
        order = OrderService.create_order(self.user.id, goods_data)

        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_amount, Decimal("200.00"))

        # Проверяем, что количество товара уменьшилось
        self.good.refresh_from_db()
        self.assertEqual(self.good.quantity, 8)  # 10 - 2

    def test_create_order_with_promo(self):
        """Тест создания заказа с промокодом"""
        goods_data = [{"good_id": self.good.id, "quantity": 1}]
        order = OrderService.create_order(self.user.id, goods_data, "TEST10")

        self.assertEqual(order.total_amount, Decimal("90.00"))  # 100 - 10%
        self.assertEqual(order.promo_code, self.promo)

    def test_create_order_insufficient_goods(self):
        """Тест ошибки при недостаточном количестве товара"""
        goods_data = [{"good_id": self.good.id, "quantity": 15}]

        with self.assertRaises(ValidationError) as context:
            OrderService.create_order(self.user.id, goods_data)

        self.assertIn("Недостаточное количество товара", str(context.exception))

    def test_create_order_user_not_found(self):
        """Тест ошибки при несуществующем пользователе"""
        goods_data = [{"good_id": self.good.id, "quantity": 1}]

        with self.assertRaises(ValidationError) as context:
            OrderService.create_order(999, goods_data)

        self.assertIn("Пользователь не найден", str(context.exception))

    def tearDown(self):
        # Очистка после каждого теста
        OrderGood.objects.all().delete()
        Order.objects.all().delete()
        PromoCode.objects.all().delete()
        Good.objects.all().delete()
        Category.objects.all().delete()
        User.objects.all().delete()
