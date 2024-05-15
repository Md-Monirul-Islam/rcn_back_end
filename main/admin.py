from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Vendor)
# admin.site.register(Product)
admin.site.register(ProductCategory)


class CustomerAdmin(admin.ModelAdmin):
    list_display = ['get_username','phone']

    def get_username(self,obj):
        return obj.user.username

admin.site.register(Customer,CustomerAdmin)

admin.site.register(OrderItems)
admin.site.register(CustomerAddress)
admin.site.register(ProductRating)

admin.site.register(ProductImage)

class ProductImagesInline(admin.StackedInline):
    model = ProductImage

class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('title',)}
    inlines = [
        ProductImagesInline,
    ]

admin.site.register(Product,ProductAdmin)

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id','customer','order_time','order_status']
admin.site.register(Order,OrderAdmin)
