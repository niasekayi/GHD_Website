from django.contrib import admin
from goodhairdaye.admin_site import ghd_admin
from .models import BannerAlert


def register(*models):
    return admin.register(*models, site=ghd_admin)


@register(BannerAlert)
class BannerAlertAdmin(admin.ModelAdmin):
    list_display  = ('message_short', 'style', 'is_active', 'created_at')
    list_editable = ('is_active',)
    list_filter   = ('style', 'is_active')
    ordering      = ['-created_at']

    fieldsets = [
        (None, {
            'fields': ('message', 'style', 'is_active'),
            'description': 'The banner appears at the top of every page while Active is checked.',
        }),
        ('Optional Button', {
            'fields': ('link_text', 'link_url'),
            'classes': ('collapse',),
            'description': 'Add a clickable button to the banner (e.g. "Book Now" linking to /book/).',
        }),
    ]

    def message_short(self, obj):
        return obj.message[:80] + ('…' if len(obj.message) > 80 else '')
    message_short.short_description = 'Message'
