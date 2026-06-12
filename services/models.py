from django.db import models


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'service categories'

    def __str__(self):
        return self.name


class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    price_display = models.CharField(max_length=100, help_text='e.g. "$120" or "From $300"')
    duration = models.CharField(max_length=100, help_text='e.g. "2 hrs"')
    description = models.TextField()
    deposit_amount = models.DecimalField(
        max_digits=8, decimal_places=2, default=50.00,
        help_text='Deposit required at booking (dollars)'
    )
    is_active = models.BooleanField(default=True)
    is_addon = models.BooleanField(default=False, help_text='Add-on only — not bookable as a standalone appointment')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['category__order', 'order', 'name']

    def __str__(self):
        return self.name

    @property
    def duration_minutes(self):
        import re
        s = self.duration.lower().strip()
        m = re.match(r'(\d+\.?\d*)\+?\s*hr', s)
        if m:
            hrs = float(m.group(1))
            if '+' in s:
                hrs += 1.0
            return int(hrs * 60)
        m = re.match(r'(\d+)\s*min', s)
        if m:
            return int(m.group(1))
        return 60
