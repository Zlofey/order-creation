from django.contrib import admin

from orders.models import Category, Good, Order, PromoCode


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    pass


@admin.register(Good)
class GoodAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass
