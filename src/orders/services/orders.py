from typing import Dict, List

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.models import User
from orders.models import Good, Order, OrderGood, PromoCode


class OrderService:
    """
    Сервис для создания заказа.
    - проверяет существование юзера
    - проверяет наличие товаров на складе
    - если товары в наличии, резервирует нужное количество
    - подсчитывает итоговую сумму заказа

    Returns:
        Объект Order
    """

    @transaction.atomic
    def create_order(self, user_id: int, goods: List[Dict], promo_code: str | None = None) -> Order:
        now = timezone.now()

        # проверяет существование юзера
        user = User.objects.filter(pk=user_id).first()
        if user is None:
            raise ValidationError("Пользователь не найден")

        promo_code_obj = None
        if promo_code:
            promo_code_obj = PromoCode.objects.filter(code=promo_code).first()
            if promo_code_obj is None:
                raise ValidationError("Промокод не найден")

            if (
                promo_code_obj.is_active is False
                or promo_code_obj.current_uses_count >= promo_code_obj.max_uses_count
            ):
                raise ValidationError("Промокод неактивен")

            if promo_code_obj.started_at > now:
                raise ValidationError("Промокод еще не начался")

            if promo_code_obj.finished_at < now:
                raise ValidationError("Промокод уже закончился")

            if Order.objects.filter(user=user, promo_code=promo_code_obj).exists():
                raise ValidationError("Вы уже использовали этот промокод")

        order = Order(user=user, promo_code=promo_code_obj)

        # Проверка товаров и их количества
        order_goods = []
        total_amount = 0
        good_objs = []
        for good in goods:
            good_obj: Good = Good.objects.filter(pk=good["good_id"]).first()
            if good_obj is None:
                raise ValidationError(f"Неверный ID товара: {good['good_id']}")

            if good_obj.quantity < good["quantity"]:
                raise ValidationError(
                    f"Недостаточно количества товара: {good_obj.name} - {good_obj.quantity}."
                )

            good_total = good["quantity"] * good_obj.price
            if good_obj.in_promo and promo_code_obj:
                total_amount += good_total - good_total * promo_code_obj.discount_percent / 100
            else:
                total_amount += good_total

            order_goods.append(
                OrderGood(
                    order=order,
                    good=good_obj,
                    quantity=good["quantity"],
                    price_at_order=good_obj.price,
                )
            )

            good_obj.quantity -= good["quantity"]
            good_objs.append(good_obj)

        order.total_amount = total_amount

        # сохраняем заказ
        order.save()

        # сохраняем товары в заказе
        OrderGood.objects.bulk_create(order_goods)

        # обновляем счетчик использования в промокоде
        promo_code_obj.current_uses_count += 1
        promo_code_obj.save(update_fields=["current_uses_count"])

        # обновляем количество товаров на складе
        Good.objects.bulk_update(good_objs, ("quantity",))

        return order


order_service = OrderService()
