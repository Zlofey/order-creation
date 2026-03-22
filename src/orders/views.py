from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from orders.serializers import OrderSerializer
from orders.services.orders import order_service


class OrderCreateView(CreateAPIView):
    """
    View создания заказа.
    """

    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        order_service.create_order(
            user_id=validated_data["user_id"],
            goods=validated_data["goods"],
            promo_code=validated_data.get("promo_code", None),
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
