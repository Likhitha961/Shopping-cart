from django.contrib import admin
from .models import Customerinbuilt
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import product,customer_cart,ShippingPayment,orders,OrderItem

class CustomerinbuiltInline(admin.StackedInline):
    model = Customerinbuilt
    can_delete = False
    verbose_name_plural = 'Customer Details'

class CustomUserAdmin(BaseUserAdmin):
    inlines = (CustomerinbuiltInline,)
    def address(self, obj):
        return obj.customerinbuilt.address if hasattr(obj, 'customerinbuilt') else ''

    def phonenumber(self, obj):
        return obj.customerinbuilt.phonenumber if hasattr(obj, 'customerinbuilt') else ''
    list_display = BaseUserAdmin.list_display + ('address', 'phonenumber')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Customerinbuilt)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(orders)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "shipping", "total_price", "paid", "createdat")
    list_filter = ("paid", "createdat")
    inlines = [OrderItemInline]
# admin.site.register(orders)
admin.site.register(product)
admin.site.register(customer_cart)

admin.site.register(ShippingPayment)
