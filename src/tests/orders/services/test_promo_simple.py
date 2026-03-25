from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError as DRFValidationError

from core.models import User
from orders.models import Category, Good, PromoCode
from orders.services.promo import PromoCodeService


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
        now = timezone.now()
        self.promo = PromoCode.objects.create(
            code="SAVE10",
            discount_percent=Decimal("0.10"),
            max_uses_count=100,
            started_at=now - timedelta(days=1),
            finished_at=now + timedelta(days=1),
        )

    def test_calculate_discount(self):
        """Тест расчета скидки"""
        discount = PromoCodeService.calculate_discount(
            good_obj=self.good, promo_code_obj=self.promo
        )
        self.assertEqual(discount, Decimal("0.10"))

    def test_promo_not_found(self):
        """Тест ошибки при несуществующем промокоде"""
        with self.assertRaises(DRFValidationError) as context:
            PromoCodeService.validate(code="NOTEXIST", user=self.user, goods=[self.good])
        self.assertIn("Промокод не найден", str(context.exception))

    def test_promo_not_for_category(self):
        """Тест промокода для другой категории"""
        other_category = Category.objects.create(name="Books")

        self.promo.category = other_category
        self.promo.save()

        discount = PromoCodeService.calculate_discount(
            good_obj=self.good, promo_code_obj=self.promo
        )

        self.assertEqual(discount, Decimal("0"))
