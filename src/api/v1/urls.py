from django.urls import include, path

urlpatterns = [
    path("orders/", include("api.v1.orders.urls"), name="orders"),
]
