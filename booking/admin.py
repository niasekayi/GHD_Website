from django.contrib import admin
from django.utils.html import format_html
from goodhairdaye.admin_site import ghd_admin
from .models import BookingSettings, WorkSchedule, BlockedDate, Appointment


def register(*models):
    return admin.register(*models, site=ghd_admin)


@register(BookingSettings)
class BookingSettingsAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ('same_day_fee_enabled', 'same_day_fee')}),
    ]

    def has_add_permission(self, request):
        return not BookingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display  = ('day_name', 'hours_display', 'is_active')
    list_editable = ('is_active',)
    ordering      = ['day_of_week']

    def day_name(self, obj):
        return obj.get_day_of_week_display()
    day_name.short_description = 'Day'

    def hours_display(self, obj):
        if obj.is_active and obj.start_time and obj.end_time:
            return f'{obj.start_time.strftime("%I:%M %p")} – {obj.end_time.strftime("%I:%M %p")}'
        return '—'
    hours_display.short_description = 'Hours'


@register(BlockedDate)
class BlockedDateAdmin(admin.ModelAdmin):
    list_display   = ('date', 'reason')
    ordering       = ['date']
    date_hierarchy = 'date'


@register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'client_name', 'service_name', 'date', 'start_time',
        'status_badge', 'payment_badge', 'deposit_due', 'created_at',
    )
    list_filter    = ('status', 'payment_status', 'is_new_client', 'date')
    search_fields  = ('client_name', 'client_email', 'client_phone')
    readonly_fields = ('created_at', 'deposit_due', 'paypal_order_id')
    ordering       = ['-date', '-start_time']
    date_hierarchy = 'date'
    list_per_page  = 25

    fieldsets = [
        ('Client', {
            'fields': ('client_name', 'client_email', 'client_phone', 'is_new_client'),
        }),
        ('Appointment', {
            'fields': ('service', 'date', 'start_time', 'end_time', 'addons_display', 'status', 'notes'),
        }),
        ('Payment', {
            'fields': ('deposit_amount', 'same_day_fee_applied', 'deposit_due',
                       'payment_status', 'paypal_order_id', 'cancellation_acknowledged'),
        }),
        ('Meta', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    ]

    def service_name(self, obj):
        return obj.service.name if obj.service else 'Consultation'
    service_name.short_description = 'Service'

    def deposit_due(self, obj):
        return f'${obj.total_deposit:.2f}'
    deposit_due.short_description = 'Total Deposit'

    def status_badge(self, obj):
        colors = {'confirmed': '#2e7d32', 'pending': '#b45309', 'cancelled': '#888'}
        color = colors.get(obj.status, '#888')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_status_display(),
        )
    status_badge.short_description = 'Status'

    def payment_badge(self, obj):
        colors = {'paid': '#2e7d32', 'pending': '#b45309', 'refunded': '#1565c0'}
        color = colors.get(obj.payment_status, '#888')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_payment_status_display(),
        )
    payment_badge.short_description = 'Payment'
