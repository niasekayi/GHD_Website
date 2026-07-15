from django.contrib import admin
from django.utils.html import format_html
from goodhairdaye.admin_site import ghd_admin
from .models import (
    ProductCategory, Product, ProductOptionGroup, ProductOptionValue, ProductImage,
    Order, OrderItem,
)


def register(*models):
    return admin.register(*models, site=ghd_admin)


class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    fields = ('name', 'price', 'stock_quantity', 'is_active', 'order')


@register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering = ['order', 'name']
    inlines = [ProductInline]


class ProductOptionValueInline(admin.TabularInline):
    model = ProductOptionValue
    extra = 0
    fields = ('label', 'price_delta', 'order')


class ProductOptionGroupInline(admin.StackedInline):
    model = ProductOptionGroup
    extra = 0
    fields = ('name', 'contributes_to_price', 'order')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ('image', 'option_value', 'order')


@register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'name', 'category', 'price', 'stock_quantity', 'is_active', 'order')
    list_editable = ('price', 'stock_quantity', 'is_active', 'order')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
    ordering = ['category__order', 'order', 'name']
    inlines = [ProductOptionGroupInline, ProductImageInline]

    fieldsets = [
        (None, {
            'fields': ('category', 'name', 'description', 'price'),
        }),
        ('Image', {
            'fields': ('image',),
        }),
        ('Inventory & Display', {
            'fields': ('stock_quantity', 'is_active', 'order'),
        }),
    ]

    def thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:40px;width:40px;object-fit:cover;border-radius:4px;" />',
                obj.image.url,
            )
        return '—'
    thumb.short_description = ''


@register(ProductOptionGroup)
class ProductOptionGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'contributes_to_price', 'order')
    list_editable = ('contributes_to_price',)
    list_filter = ('product', 'contributes_to_price')
    inlines = [ProductOptionValueInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'selected_options', 'unit_price', 'quantity', 'line_total')
    can_delete = False


@register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'total', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status')
    search_fields = ('order_number', 'customer_name', 'customer_email')
    readonly_fields = ('order_number', 'paypal_order_id', 'subtotal', 'total', 'created_at')
    inlines = [OrderItemInline]
    ordering = ['-created_at']
