import random
import string
from datetime import date

from django.db import models


class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'product categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='shop/', blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category__order', 'order', 'name']

    def __str__(self):
        return self.name

    @property
    def in_stock(self):
        return self.stock_quantity > 0

    @property
    def has_options(self):
        return self.option_groups.exists()

    @property
    def price_range(self):
        """(min_price, max_price). If any combination-specific prices (ProductVariant) are
        set, uses those. Otherwise falls back to base price +/- per-option deltas."""
        variants = list(self.variants.all())
        if variants:
            prices = [v.price for v in variants]
            return (min(prices), max(prices))
        low = high = self.price
        for group in self.option_groups.all():
            deltas = [v.price_delta for v in group.values.all()]
            if deltas:
                low += min(deltas)
                high += max(deltas)
        return (low, high)


class ProductOptionGroup(models.Model):
    """A choice the customer must make, e.g. 'Hair Texture' or 'Hair Length'."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='option_groups')
    name = models.CharField(max_length=100, help_text='e.g. "Hair Texture" or "Hair Length"')
    contributes_to_price = models.BooleanField(
        default=False,
        help_text='Check this if selecting a value in this group changes the price (e.g. Hair Length). Leave unchecked for purely descriptive options like Hair Texture.',
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.product.name} — {self.name}'


class ProductOptionValue(models.Model):
    """One selectable value within an option group, e.g. 'Kinky Curly'."""
    group = models.ForeignKey(ProductOptionGroup, on_delete=models.CASCADE, related_name='values')
    label = models.CharField(max_length=100)
    price_delta = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text='Added to (or subtracted from) the base price when this is selected. Leave 0 if price does not change.'
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.label


class ProductVariant(models.Model):
    """An explicit price for one specific combination of option values, e.g.
    Texture=Juicy Curly + Length=18 inch -> $100. Overrides the additive per-value
    price_delta for that exact combination. A combination only needs a ProductVariant
    if its price doesn't follow the simple additive formula."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    option_values = models.ManyToManyField(ProductOptionValue, related_name='variants')
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        labels = ' / '.join(v.label for v in self.option_values.all())
        return f'{self.product.name} ({labels}) — ${self.price}'


class ProductImage(models.Model):
    """An additional photo for a product. Optionally tied to one option value, in which case
    selecting that option swaps the displayed photo on the product page."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='shop/gallery/')
    option_value = models.ForeignKey(
        ProductOptionValue, on_delete=models.SET_NULL, null=True, blank=True, related_name='images',
        help_text='Optional — show this photo automatically when this option is selected'
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.product.name} photo {self.pk}'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)

    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=30)
    shipping_address_line1 = models.CharField(max_length=255)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=50)
    shipping_zip = models.CharField(max_length=20)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    paypal_order_id = models.CharField(max_length=100, blank=True, default='')
    stock_restored = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order {self.order_number} — {self.customer_name}'

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_order_number():
        prefix = f'GHD{date.today().strftime("%y%m")}'
        for _ in range(10):
            candidate = prefix + ''.join(random.choices(string.digits, k=5))
            if not Order.objects.filter(order_number=candidate).exists():
                return candidate
        raise RuntimeError('Could not generate a unique order number.')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField()
    selected_options = models.CharField(
        max_length=300, blank=True, default='',
        help_text='e.g. "Hair Texture: Kinky Curly, Hair Length: 16in"'
    )

    def __str__(self):
        return f'{self.quantity} × {self.product_name}'

    @property
    def line_total(self):
        return self.unit_price * self.quantity
