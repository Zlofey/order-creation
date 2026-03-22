from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import TimestampModel, User


class Category(TimestampModel):
    """Категория товаров."""

    name = models.CharField(max_length=255, unique=True, verbose_name="Название")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Good(TimestampModel):
    """Модель товара."""

    name = models.CharField(max_length=255, verbose_name="Наименование")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="goods", verbose_name="Категория"
    )
    quantity = models.PositiveSmallIntegerField(default=0, verbose_name="Количество")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Цена",
    )
    in_promo = models.BooleanField(default=True, verbose_name="Участвует в акциях")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"


class PromoCode(TimestampModel):
    """
    Модель промокода.

    Правила применения промокода:
        - Промокод должен существовать;
        - Промокод не должен быть просрочен;
        - У промокода есть ограничение на максимальное количество использований;
        - Один пользователь не может использовать один и тот же промокод более одного раза;
        - Промокод может быть ограничен определенной категорией товаров;
        - Некоторые товары могут быть исключены из любых акций,
        к ним промокод не должен применяться.
    """

    code = models.CharField(max_length=32, unique=True, verbose_name="Код")
    discount_percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)], verbose_name="Процент скидки"
    )
    max_uses_count = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Максимальное количество использований",
    )
    current_uses_count = models.PositiveSmallIntegerField(verbose_name="Количество использований")
    started_at = models.DateTimeField(verbose_name="Начало акции")
    finished_at = models.DateTimeField(verbose_name="Окончание акции")
    category = models.ForeignKey(
        Category,
        related_name="promo_codes",
        on_delete=models.CASCADE,
        verbose_name="Категория",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"


class Order(TimestampModel):
    """Модель заказа."""

    user = models.ForeignKey(
        User,
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
    promo_applied = models.BooleanField(default=False, verbose_name="Промокод применен")
    discount_percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)], verbose_name="Процент скидки"
    )

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"
        unique_together = (("order", "good"),)
