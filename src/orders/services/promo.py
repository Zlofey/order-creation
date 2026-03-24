from decimal import Decimal
from typing import List

from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.models import User
from orders.models import Good, Order, PromoCode


class PromoCodeService:

    @classmethod
    def _get_promo_code_object(cls, code: str) -> PromoCode:
        promo_code_obj = PromoCode.objects.filter(code=code).first()
        if promo_code_obj is None:
            raise ValidationError("Промокод не найден")
        return promo_code_obj

    @classmethod
    def _is_valid_by_time(cls, promo_code_obj: PromoCode) -> None:
        """
        Проверяет временные рамки промокода.

        Raises:
            ValidationError: если промокод ещё не активен или уже истёк
        """
        now = timezone.now()
        if promo_code_obj.started_at > now:
            raise ValidationError("Промокод еще не начался")

        if promo_code_obj.finished_at <= now:
            raise ValidationError("Промокод уже закончился")

    @classmethod
    def is_applicable_to_good(cls, promo_code_obj: PromoCode, good_obj: Good) -> bool:
        """
        Проверка, применим ли промокод к товару?

        Товар должен участвовать в акции.
        Если у промокода указана категория, категория товара должна совпадать.
        Если у промокода нет категории, промокод применяется ко всем товарам.
        """
        # участвует ли товар в акции
        if not good_obj.in_promo:
            return False

        # промокод с категорией, проверяем совпадение
        if promo_code_obj.category is not None:
            return good_obj.category == promo_code_obj.category
        # Промокод без категории
        return True

    @classmethod
    def _is_applicable_to_any_good(cls, promo_code_obj: PromoCode, goods: list[Good]) -> bool:
        """Проверяет, применим ли промокод к какому-либо товару."""
        return any(cls.is_applicable_to_good(promo_code_obj, good) for good in goods)

    @classmethod
    def validate(cls, code: str, user: User, goods: List[Good]) -> PromoCode:
        """Полная валидация промокода перед применением."""

        # проверка на существование промокода
        promo_code_obj = cls._get_promo_code_object(code)

        # проверка, что промокод активен
        if not promo_code_obj.is_active:
            raise ValidationError("Промокод неактивен")

        # проверка на временные рамки
        cls._is_valid_by_time(promo_code_obj)

        # проверка на лимит использований
        if promo_code_obj.current_uses_count >= promo_code_obj.max_uses_count:
            raise ValidationError("Промокод неактивен")

        # проверка, что юзер уже использовал промокод
        if Order.objects.filter(user=user, promo_code=promo_code_obj).exists():
            raise ValidationError("Вы уже использовали этот промокод")

        # проверка по категории
        if not cls._is_applicable_to_any_good(promo_code_obj, goods):
            raise ValidationError("Промокод не применим к товарам в этом заказе.")

        return promo_code_obj

    @classmethod
    def calculate_discount(cls, good_obj: Good, promo_code_obj: PromoCode) -> Decimal:
        """Рассчитывает процент скидки для конкретного товара."""
        if cls.is_applicable_to_good(promo_code_obj=promo_code_obj, good_obj=good_obj):
            return promo_code_obj.discount_percent
        return Decimal("0")

    @classmethod
    def increment_usage(cls, promo_id: int) -> None:
        """Атомарно увеличивает счётчик использований промокода."""
        updated = PromoCode.objects.filter(
            pk=promo_id, current_uses_count__lt=F("max_uses_count")
        ).update(current_uses_count=F("current_uses_count") + 1)
        if updated == 0:
            raise ValidationError("Лимит использований промокода исчерпан")
