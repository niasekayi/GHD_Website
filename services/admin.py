from django.contrib import admin
from goodhairdaye.admin_site import ghd_admin
from .models import ServiceCategory, Service


def register(*models):
    return admin.register(*models, site=ghd_admin)


class ServiceInline(admin.TabularInline):
    model  = Service
    extra  = 0
    fields = ('name', 'price_display', 'duration', 'deposit_amount', 'is_active', 'is_addon', 'order')


@register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering     = ['order', 'name']
    inlines      = [ServiceInline]


@register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display  = ('name', 'category', 'price_display', 'duration', 'deposit_amount', 'is_addon', 'is_active', 'order')
    list_filter   = ('category', 'is_active', 'is_addon')
    list_editable = ('price_display', 'deposit_amount', 'is_active', 'is_addon', 'order')
    search_fields = ('name',)
    ordering      = ['category__order', 'order', 'name']
    fieldsets = [
        (None, {
            'fields': ('category', 'name', 'price_display', 'duration', 'description'),
        }),
        ('Settings', {
            'fields': ('deposit_amount', 'is_active', 'is_addon', 'order'),
        }),
    ]
