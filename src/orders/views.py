from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from orders.serializers import OrderCreateResponseSerializer, OrderSerializer
from orders.services.orders import OrderService


class OrderCreateView(CreateAPIView):
    """
    View создания заказа.
    """

    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        created_obj = OrderService.create_order(
            user_id=validated_data["user_id"],
            goods_data=validated_data["goods"],
            code=validated_data.get("promo_code", None),
        )
        resp_data = OrderCreateResponseSerializer(created_obj).data
        return Response(resp_data, status=status.HTTP_201_CREATED)
