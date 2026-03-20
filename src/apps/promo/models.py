from django.core.validators import MinValueValidator
from django.db import models

from apps.catalog.models import Category
from core.models import TimestampModel


# Create your models here.
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
        blank=True,
        verbose_name="Категория",
    )

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"
