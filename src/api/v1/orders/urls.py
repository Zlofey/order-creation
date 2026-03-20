from django.urls import path

from api.v1.orders.views import OrderCreateView

urlpatterns = [
    path("", OrderCreateView.as_view(), name="order-create"),
]
