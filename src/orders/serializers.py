from rest_framework import serializers


class GoodSerializer(serializers.Serializer):
    good_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class OrderSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    goods = GoodSerializer(
        many=True,
        allow_empty=False,
        error_messages={"empty": "Добавьте хотя бы один товар в заказ."},
    )
    promo_code = serializers.CharField(max_length=32, required=False)

    def validate_goods(self, value):
        """Проверяет, что в списке товаров нет дубликатов по good_id."""
        good_ids = [item["good_id"] for item in value]
        if len(good_ids) != len(set(good_ids)):
            raise serializers.ValidationError("Список товаров содержит дубликаты.")
        return value


class OrderCreateResponseLineSerializer(serializers.Serializer):
    good_id = serializers.IntegerField(source="good.id")
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, source="price_at_order")
    discount = serializers.DecimalField(max_digits=3, decimal_places=2, source="discount_percent")
    total = serializers.DecimalField(max_digits=10, decimal_places=2, source="subtotal")


class OrderCreateResponseSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    order_id = serializers.IntegerField(source="id")
    goods = OrderCreateResponseLineSerializer(many=True, source="order_goods")
    price = serializers.DecimalField(max_digits=10, decimal_places=2, source="total_price")
    discount = serializers.DecimalField(
        max_digits=3, decimal_places=2, source="total_discount_percent"
    )
    total = serializers.DecimalField(max_digits=10, decimal_places=2, source="total_amount")
