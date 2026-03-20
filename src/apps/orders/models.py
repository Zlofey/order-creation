from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.catalog.models import Good
from apps.promo.models import PromoCode
from core.models import TimestampModel


class Order(TimestampModel):
    """Модель заказа."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Покупатель",
    )
    goods = models.ManyToManyField(Good, through="OrderGood", verbose_name="Товары")
    promo_code = models.ForeignKey(
        PromoCode, on_delete=models.SET_NULL, null=True, verbose_name="Промокод"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Общая сумма",
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        unique_together = (("user", "promo_code"),)


class OrderGood(TimestampModel):
    """Модель позиции заказа."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_goods", verbose_name="Заказ"
    )
    good = models.ForeignKey(
        Good, on_delete=models.CASCADE, related_name="order_goods", verbose_name="Товар"
    )
    quantity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)], verbose_name="Количество"
    )
    price_at_order = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Цена на момент заказа",
    )

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"
        unique_together = (("order", "good"),)
