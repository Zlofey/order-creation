from rest_framework.generics import CreateAPIView

from orders.models import Order


class OrderCreateView(CreateAPIView):
    queryset = Order.objects.all()
