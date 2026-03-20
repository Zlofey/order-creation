from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from core.models import TimestampModel


# Create your models here.
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
