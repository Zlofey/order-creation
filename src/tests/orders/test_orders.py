from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import User
from orders.models import Category, Good, PromoCode
from orders.services.orders import OrderService
from orders.services.promo import PromoCodeService


class OrderServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.category = Category.objects.create(name="Electronics")
        self.good = Good.objects.create(
            name="Phone", category=self.category, quantity=10, price=Decimal("100.00")
        )

    def test_create_order_success(self):
        """Тест успешного создания заказа"""
        goods_data = [{"good_id": self.good.id, "quantity": 2}]
        order = OrderService.create_order(self.user.id, goods_data)

        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_amount, Decimal("200.00"))
        self.assertEqual(self.good.quantity, 8)  # 10 - 2

    def test_create_order_with_promo(self):
        """Тест создания заказа с промокодом"""
        promo = PromoCode.objects.create(
            code="TEST10",
            discount_percent=Decimal("0.10"),
            max_uses_count=100,
            started_at="2024-01-01T00:00:00Z",
            finished_at="2025-12-31T23:59:59Z",
        )

        goods_data = [{"good_id": self.good.id, "quantity": 1}]
        OrderService.create_order(self.user.id, goods_data, "TEST10")

        self.assertEqual(promo.discount_percent, Decimal("0.10"))

    def test_create_order_insufficient_goods(self):
        """Тест ошибки при недостаточном количестве товара"""
        goods_data = [{"good_id": self.good.id, "quantity": 15}]

        with self.assertRaises(ValidationError) as context:
            OrderService.create_order(self.user.id, goods_data)

        self.assertIn("Недостаточное количество", str(context.exception))

    def test_create_order_user_not_found(self):
        """Тест ошибки при несуществующем пользователе"""
        goods_data = [{"good_id": self.good.id, "quantity": 1}]

        with self.assertRaises(ValidationError) as context:
            OrderService.create_order(999, goods_data)

        self.assertEqual(str(context.exception), "Пользователь не найден")


class PromoCodeServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.category = Category.objects.create(name="Electronics")
        self.good = Good.objects.create(
            name="Phone",
            category=self.category,
            quantity=10,
            price=Decimal("100.00"),
            in_promo=True,
        )
        self.promo = PromoCode.objects.create(
            code="SAVE10",
            discount_percent=Decimal("0.10"),
            max_uses_count=100,
            started_at="2024-01-01T00:00:00Z",
            finished_at="2025-12-31T23:59:59Z",
        )

    def test_validate_promo_success(self):
        """Т успешной валидации промокода"""
        promo = PromoCodeService.validate(code="SAVE10", user=self.user, goods=[self.good])

        self.assertEqual(promo, self.promo)

    def test_validate_promo_expired(self):
        """Тест ошибки при просроченном промокоде"""
        self.promo.finished_at = "2023-12-31T23:59:59Z"
        self.promo.save()

        with self.assertRaises(ValidationError) as context:
            PromoCodeService.validate(code="SAVE10", user=self.user, goods=[self.good])

        self.assertIn("Промокод просрочен", str(context.exception))

    def test_validate_promo_max_uses(self):
        """Тест ошибки при превышении лимита использований"""
        self.promo.current_uses_count = self.promo.max_uses_count
        self.promo.save()

        with self.assertRaises(ValidationError) as context:
            PromoCodeService.validate(code="SAVE10", user=self.user, goods=[self.good])

        self.assertIn("Превышен лимит использований", str(context.exception))

    def test_calculate_discount(self):
        """Тест расчета скидки"""
        discount = PromoCodeService.calculate_discount(
            good_obj=self.good, promo_code_obj=self.promo
        )

        self.assertEqual(discount, Decimal("0.10"))


class OrderAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.category = Category.objects.create(name="Electronics")
        self.good = Good.objects.create(
            name="Phone", category=self.category, quantity=10, price=Decimal("100.00")
        )

    def test_create_order_api_success(self):
        """Тест успешного создания заказа через API"""
        data = {"user_id": self.user.id, "goods": [{"good_id": self.good.id, "quantity": 2}]}

        response = self.client.post("/orders/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user_id"], self.user.id)
        self.assertEqual(len(response.data["goods"]), 1)
        self.assertEqual(response.data["goods"][0]["good_id"], self.good.id)
        self.assertEqual(response.data["goods"][0]["quantity"], 2)
        self.assertEqual(float(response.data["total"]), 200.0)

    def test_create_order_api_empty_goods(self):
        """Тест ошибки при пустом списке товаров"""
        data = {"user_id": self.user.id, "goods": []}

        response = self.client.post("/orders/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
