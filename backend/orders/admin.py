from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_id', 'name', 'detail', 'quantity', 'unit_price', 'note')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('public_id', 'customer_name', 'status', 'pickup_at', 'total', 'payment')
    list_filter = ('status', 'payment', 'pickup_at')
    search_fields = ('public_id', 'customer_name', 'email', 'phone')
    readonly_fields = ('public_id', 'placed_at', 'subtotal', 'tax', 'total')
    inlines = (OrderItemInline,)
