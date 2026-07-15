from django.db import models


class GalleryPhoto(models.Model):
    image      = models.ImageField(upload_to='gallery/')
    caption    = models.CharField(max_length=200, blank=True)
    service    = models.ForeignKey(
        'services.Service', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='gallery_photos',
        help_text='Optional — link to a service to show a "Book This Style" button'
    )
    order      = models.PositiveIntegerField(default=0)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.caption or f'Photo {self.pk}'


class Review(models.Model):
    client_name = models.CharField(max_length=100)
    rating      = models.PositiveSmallIntegerField(default=5)
    body        = models.TextField()
    photo       = models.ImageField(upload_to='reviews/', blank=True, null=True)
    video_url   = models.URLField(blank=True, help_text='YouTube or direct video URL')
    is_active   = models.BooleanField(default=True)
    order       = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return f'{self.client_name} — {self.rating}★'


class BannerAlert(models.Model):
    STYLE_CHOICES = [
        ('promo', 'Promo — Gold'),
        ('info',  'Info — Tan'),
        ('deal',  'Deal — Green'),
    ]
    message    = models.CharField(max_length=300, help_text='Text shown in the banner across the top of every page.')
    link_text  = models.CharField(max_length=100, blank=True, help_text='Optional button text, e.g. "Book Now"')
    link_url   = models.CharField(max_length=200, blank=True, help_text='Optional URL the button links to')
    style      = models.CharField(max_length=20, choices=STYLE_CHOICES, default='promo')
    is_active  = models.BooleanField(default=True, help_text='Check to show this banner on the site right now.')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Banner / Announcement'
        verbose_name_plural = 'Banners & Announcements'

    def __str__(self):
        status = 'Active' if self.is_active else 'Inactive'
        return f'[{status}] {self.message[:70]}'
