from django.contrib import admin
from .models import BookingSettings, WorkSchedule, BlockedDate, Appointment


@admin.register(BookingSettings)
class BookingSettingsAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ('same_day_fee_enabled', 'same_day_fee')}),
    ]

    def has_add_permission(self, request):
        return not BookingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ('day_name', 'hours_display', 'is_active')
    list_editable = ('is_active',)
    ordering = ['day_of_week']

    def day_name(self, obj):
        return obj.get_day_of_week_display()
    day_name.short_description = 'Day'

    def hours_display(self, obj):
        if obj.is_active and obj.start_time and obj.end_time:
            return f'{obj.start_time.strftime("%I:%M %p")} – {obj.end_time.strftime("%I:%M %p")}'
        return '—'
    hours_display.short_description = 'Hours'


@admin.register(BlockedDate)
class BlockedDateAdmin(admin.ModelAdmin):
    list_display = ('date', 'reason')
    ordering = ['date']
    date_hierarchy = 'date'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'client_name', 'service', 'date', 'start_time',
        'status', 'is_new_client', 'same_day_fee_applied', 'deposit_due', 'created_at'
    )
    list_filter = ('status', 'is_new_client', 'same_day_fee_applied', 'date')
    search_fields = ('client_name', 'client_email', 'client_phone')
    readonly_fields = ('created_at', 'deposit_due')
    ordering = ['-date', '-start_time']
    date_hierarchy = 'date'

    fieldsets = [
        ('Client', {'fields': ('client_name', 'client_email', 'client_phone', 'is_new_client')}),
        ('Appointment', {'fields': ('service', 'date', 'start_time', 'end_time', 'status', 'notes')}),
        ('Payment', {'fields': ('deposit_amount', 'same_day_fee_applied', 'cancellation_acknowledged', 'deposit_due')}),
        ('Meta', {'fields': ('created_at',)}),
    ]

    def deposit_due(self, obj):
        return f'${obj.total_deposit:.2f}'
    deposit_due.short_description = 'Total Deposit Due'
