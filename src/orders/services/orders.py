from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List

from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError

from core.models import User
from orders.models import Good, Order, OrderGood, PromoCode
from orders.services.promo import PromoCodeService


class OrderService:
    MONEY_QUANT = Decimal("0.01")

    """
    Сервис для создания заказа.
    - проверяет существование юзера
    - проверяет наличие товаров на складе
    - если товары в наличии, резервирует нужное количество
    - подсчитывает итоговую сумму заказа

    Returns:
        Объект Order
    """

    @classmethod
    def _get_goods(cls, goods_data: List[Dict]) -> List[Good]:
        """
        Возвращает список объектов товаров.

        Raises:
            ValidationError: если какой-то товар не найден
        """
        good_ids = [g["good_id"] for g in goods_data]
        goods = list(Good.objects.select_related("category").filter(id__in=good_ids))

        found_ids = {g.id for g in goods}
        # получаем id не найденных в бд товаров
        missing_ids = set(good_ids) - found_ids
        if missing_ids:
            raise ValidationError(f"Товары с id {missing_ids} не найдены.")
        return goods

    @classmethod
    def _get_user(cls, user_id: int) -> User:
        user = User.objects.filter(pk=user_id).first()
        if user is None:
            raise ValidationError("Пользователь не найден")
        return user

    @classmethod
    def _goods_reserve(cls, goods_data: List[Dict]) -> None:
        """
        Проверяет и резервирует нужные количества товаров на складе.
        Args:
            goods_data: id товара и количество
        Raises:
            ValidationError: если какого-то товара недостаточно
        """
        for item in goods_data:
            updated = Good.objects.filter(
                pk=item["good_id"], quantity__gte=item["quantity"]
            ).update(quantity=F("quantity") - item["quantity"])
            if updated != 1:
                good = Good.objects.get(pk=item["good_id"])
                raise ValidationError(
                    f"Недостаточное количество товара {good.name}:"
                    f" в наличии - {good.quantity}, требуется - {item['quantity']}"
                )

    @classmethod
    def create_order_good(
        cls, good: Good, order: Order, qty: int, promo_code: PromoCode | None = None
    ) -> OrderGood:
        """Создает объект продукт-в-заказе."""
        # расчет процента скидки на товар
        discount_percent = Decimal("0")
        if promo_code:
            discount_percent = PromoCodeService.calculate_discount(
                good_obj=good,
                promo_code_obj=promo_code,
            )
        subtotal = (Decimal(qty) * good.price * (Decimal("1") - discount_percent)).quantize(
            cls.MONEY_QUANT, rounding=ROUND_HALF_UP
        )
        return OrderGood(
            order=order,
            good=good,
            quantity=qty,
            price_at_order=good.price,
            discount_percent=discount_percent,
            subtotal=subtotal,
        )

    @classmethod
    def add_goods_to_order(
        cls,
        goods: list[Good],
        goods_data: list[dict],
        order: Order,
        promo_code: PromoCode | None = None,
    ) -> tuple[list[Any], Decimal]:
        """
        Добавляет позиции к заказу.

        Подчитывает итоговую сумму заказа.
        """
        goods_dict = {g.pk: g for g in goods}
        order_goods = []
        total_amount = Decimal("0")
        for item in goods_data:
            good_obj = goods_dict[item["good_id"]]
            order_good = cls.create_order_good(
                good=good_obj, order=order, qty=item["quantity"], promo_code=promo_code
            )
            order_goods.append(order_good)
            total_amount += order_good.subtotal
        return order_goods, total_amount.quantize(cls.MONEY_QUANT, rounding=ROUND_HALF_UP)

    @classmethod
    @transaction.atomic
    def create_order(cls, user_id: int, goods_data: List[Dict], code: str | None = None) -> Order:
        """
        Создает заказ.

        Args:
            user_id: id покупателя
            goods_data: товары для заказа
            code: строка промокода

        Returns:
            объект Order
        """
        # находим покупателя
        user = cls._get_user(user_id)

        # находим объекты товаров
        goods = cls._get_goods(goods_data)

        # валидация промокода
        promo_code = None
        if code:
            promo_code = PromoCodeService.validate(
                code=code,
                user=user,
                goods=goods,
            )

        # резервирование товаров
        cls._goods_reserve(goods_data)

        # создание объекта заказа
        order = Order(user=user, promo_code=promo_code)

        # добавляем позиции в заказ
        order_goods, total_amount = cls.add_goods_to_order(goods, goods_data, order, promo_code)

        # проставляем итоговую сумму в заказ
        order.total_amount = total_amount

        # сохраняем заказ
        order.save()

        # сохраняем товары в заказе
        OrderGood.objects.bulk_create(order_goods)

        # обновляем счетчик использований в промокоде
        if promo_code:
            PromoCodeService.increment_usage(promo_code.id)

        return order
