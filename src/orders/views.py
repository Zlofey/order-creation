from rest_framework.response import Response
from rest_framework.views import APIView

from orders.serializers import OrderSerializer

# class OrderCreateView(CreateAPIView):
#     queryset = Order.objects.all()


class OrderCreateView(APIView):
    """
    Заглушка для будущей View по созданию заказа.
    """

    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        serializer.is_valid()
        return Response(serializer.data)
