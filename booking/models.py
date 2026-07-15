import re
from datetime import datetime, timedelta
from django.db import models


class BookingSettings(models.Model):
    same_day_fee = models.DecimalField(max_digits=6, decimal_places=2, default=75.00)
    same_day_fee_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Booking Settings'
        verbose_name_plural = 'Booking Settings'

    def __str__(self):
        return 'Booking Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class WorkSchedule(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    day_of_week = models.IntegerField(choices=DAY_CHOICES, unique=True)
    start_time = models.TimeField(null=True, blank=True, help_text='Leave blank if closed this day')
    end_time = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text='Uncheck to close this day')

    class Meta:
        ordering = ['day_of_week']
        verbose_name = 'Work Schedule'
        verbose_name_plural = 'Work Schedule'

    def __str__(self):
        if self.is_active and self.start_time and self.end_time:
            return f'{self.get_day_of_week_display()}: {self.start_time.strftime("%I:%M %p")} – {self.end_time.strftime("%I:%M %p")}'
        return f'{self.get_day_of_week_display()}: Closed'


class BlockedDate(models.Model):
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['date']
        verbose_name = 'Blocked Date'
        verbose_name_plural = 'Blocked Dates'

    def __str__(self):
        return f'{self.date} — {self.reason or "Blocked"}'


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    service = models.ForeignKey(
        'services.Service', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='appointments'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    client_name = models.CharField(max_length=200)
    client_email = models.EmailField()
    client_phone = models.CharField(max_length=30)
    is_new_client = models.BooleanField(default=False)

    deposit_amount = models.DecimalField(max_digits=8, decimal_places=2)
    same_day_fee_applied = models.BooleanField(default=False)
    cancellation_acknowledged = models.BooleanField(default=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    addons_display = models.TextField(blank=True, default='', help_text='Selected add-on service names, comma-separated')
    reminder_sent = models.BooleanField(default=False)

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]
    paypal_order_id = models.CharField(max_length=100, blank=True, default='')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        service_name = self.service.name if self.service else 'Consultation'
        return f'{self.client_name} — {service_name} ({self.date} {self.start_time.strftime("%I:%M %p")})'

    @property
    def total_deposit(self):
        total = self.deposit_amount
        if self.same_day_fee_applied:
            total += BookingSettings.get().same_day_fee
        return total
