from django.urls import path

from orders.views import OrderCreateView

urlpatterns = [
    path("", OrderCreateView.as_view(), name="order-create"),
]
