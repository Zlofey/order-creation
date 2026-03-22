from rest_framework import serializers


class GoodSerializer(serializers.Serializer):
    good_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class OrderSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    goods = GoodSerializer(many=True)
    promo_code = serializers.CharField(max_length=32, required=False)
