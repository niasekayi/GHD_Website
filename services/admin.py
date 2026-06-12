from django.contrib import admin
from .models import ServiceCategory, Service


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 0
    fields = ('name', 'price_display', 'duration', 'deposit_amount', 'is_active', 'order')


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering = ['order', 'name']
    inlines = [ServiceInline]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price_display', 'duration', 'deposit_amount', 'is_active', 'order')
    list_filter = ('category', 'is_active')
    list_editable = ('is_active', 'order')
    search_fields = ('name',)
    ordering = ['category__order', 'order', 'name']
