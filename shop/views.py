import json
import re

from django.conf import settings
from django.db import models, transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from goodhairdaye.paypal_utils import _paypal_access_token, _paypal_post
from .models import ProductCategory, Product, ProductOptionValue, ProductVariant, Order, OrderItem


def index(request):
    categories = ProductCategory.objects.prefetch_related(
        models.Prefetch(
            'products',
            queryset=Product.objects.filter(is_active=True).prefetch_related(
                'option_groups__values', 'gallery_images__option_value', 'variants__option_values',
            ),
        )
    ).order_by('order', 'name')

    for cat in categories:
        for product in cat.products.all():
            groups = [
                {
                    'id': g.id,
                    'name': g.name,
                    'contributes_to_price': g.contributes_to_price,
                    'values': [
                        {'id': v.id, 'label': v.label, 'price_delta': float(v.price_delta)}
                        for v in g.values.all()
                    ],
                }
                for g in product.option_groups.all()
            ]
            gallery = [
                {'id': img.id, 'url': img.image.url, 'option_value_id': img.option_value_id}
                for img in product.gallery_images.all()
            ]
            variants = [
                {'value_ids': sorted(v.id for v in var.option_values.all()), 'price': float(var.price)}
                for var in product.variants.all()
            ]
            product.options_json  = json.dumps(groups)
            product.gallery_json  = json.dumps(gallery)
            product.variants_json = json.dumps(variants)
            product.price_low, product.price_high = product.price_range

    return render(request, 'shop/index.html', {'categories': categories})


def _parse_cart_items(raw_items):
    """Normalize the client-supplied cart payload to a list of dicts:
    {id, qty, option_value_ids: [int, ...]}. Raises ValueError on malformed input."""
    items = []
    for raw in raw_items or []:
        pid = int(raw['id'])
        qty = int(raw['qty'])
        if qty <= 0:
            raise ValueError('Quantity must be positive.')
        option_value_ids = [int(v) for v in (raw.get('option_value_ids') or [])]
        items.append({'id': pid, 'qty': qty, 'option_value_ids': option_value_ids})
    if not items:
        raise ValueError('Your cart is empty.')
    return items


def _resolve_item_options(product, option_value_ids):
    """Validate that option_value_ids cover exactly one value per option group on this
    product, with no unknown values. Returns (unit_price, summary_text)."""
    groups = list(product.option_groups.all())
    if not groups:
        if option_value_ids:
            raise ValueError(f'"{product.name}" does not have any selectable options.')
        return product.price, ''

    values = {v.id: v for v in ProductOptionValue.objects.filter(id__in=option_value_ids, group__product=product)}
    if len(values) != len(option_value_ids):
        raise ValueError(f'One of the selected options for "{product.name}" is no longer available.')

    chosen_by_group = {}
    for v in values.values():
        if v.group_id in chosen_by_group:
            raise ValueError(f'Only one choice is allowed per option for "{product.name}".')
        chosen_by_group[v.group_id] = v

    missing = [g.name for g in groups if g.id not in chosen_by_group]
    if missing:
        raise ValueError(f'Please choose a {missing[0]} for "{product.name}".')

    selected_ids = frozenset(chosen_by_group[g.id].id for g in groups)

    # Check for a variant-level exact combination price (overrides additive deltas)
    unit_price = None
    for variant in product.variants.prefetch_related('option_values').all():
        if frozenset(ov.id for ov in variant.option_values.all()) == selected_ids:
            unit_price = variant.price
            break

    if unit_price is None:
        unit_price = product.price
        for g in groups:
            unit_price += chosen_by_group[g.id].price_delta

    summary_parts = [f'{g.name}: {chosen_by_group[g.id].label}' for g in groups]
    return unit_price, ', '.join(summary_parts)


def _validate_stock(items):
    """Given [{id, qty, option_value_ids}], load active Products, validate option
    selections, and check stock. Returns (products_by_id, line_data, subtotal) or
    raises ValueError with a customer-facing message.
    line_data is a list of (product, qty, unit_price, options_summary)."""
    product_ids = [item['id'] for item in items]
    products = {
        p.id: p for p in
        Product.objects.filter(id__in=product_ids, is_active=True).prefetch_related('option_groups__values', 'variants__option_values')
    }

    subtotal = 0
    line_data = []
    for item in items:
        product = products.get(item['id'])
        if not product:
            raise ValueError('One of the items in your cart is no longer available.')
        if product.stock_quantity < item['qty']:
            raise ValueError(f'Only {product.stock_quantity} left of "{product.name}". Please update your cart.')
        unit_price, options_summary = _resolve_item_options(product, item['option_value_ids'])
        subtotal += unit_price * item['qty']
        line_data.append((product, item['qty'], unit_price, options_summary))
    return products, line_data, subtotal


@require_POST
def api_create_paypal_order(request):
    """body: {items: [{id, qty}]}. Recomputes total server-side from live prices/stock.
    Returns {order_id, total} or {error}."""
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_SECRET:
        return JsonResponse({'error': 'Payment is not configured yet. Please contact us to order.'}, status=503)
    try:
        data = json.loads(request.body)
        items = _parse_cart_items(data.get('items'))
        _, _, subtotal = _validate_stock(items)

        token = _paypal_access_token()
        status_code, order = _paypal_post(
            '/v2/checkout/orders',
            token,
            {
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'amount': {'currency_code': 'USD', 'value': f'{subtotal:.2f}'},
                    'description': 'Good Hair Daye Shop Order',
                }],
                'application_context': {
                    'brand_name': 'Good Hair Daye',
                    'user_action': 'PAY_NOW',
                    'shipping_preference': 'NO_SHIPPING',
                },
            },
        )

        if status_code != 201 or 'id' not in order:
            return JsonResponse({'error': 'Could not create payment order. Please try again.'}, status=502)

        return JsonResponse({'order_id': order['id'], 'total': f'{subtotal:.2f}'})

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def api_capture_order(request):
    """body: {paypal_order_id, items: [{id, qty}], customer_name, customer_email, customer_phone,
    shipping_address_line1, shipping_address_line2, shipping_city, shipping_state, shipping_zip}.
    Order is only created in the DB once PayPal capture succeeds."""
    try:
        data = json.loads(request.body)

        paypal_order_id = data.get('paypal_order_id', '').strip()
        customer_name = data.get('customer_name', '').strip()
        customer_email = data.get('customer_email', '').strip()
        customer_phone = data.get('customer_phone', '').strip()
        address_line1 = data.get('shipping_address_line1', '').strip()
        address_line2 = data.get('shipping_address_line2', '').strip()
        city = data.get('shipping_city', '').strip()
        state = data.get('shipping_state', '').strip()
        zip_code = data.get('shipping_zip', '').strip()

        if not all([paypal_order_id, customer_name, customer_email, customer_phone,
                    address_line1, city, state, zip_code]):
            return JsonResponse({'error': 'Please fill in all required fields.'}, status=400)
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', customer_email):
            return JsonResponse({'error': 'Please enter a valid email address.'}, status=400)

        items = _parse_cart_items(data.get('items'))

        # Cheap, reversible check before touching payment.
        try:
            _validate_stock(items)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=409)

        # Capture the PayPal payment — the order is only created on success.
        try:
            token = _paypal_access_token()
            capture_status, capture_data = _paypal_post(
                f'/v2/checkout/orders/{paypal_order_id}/capture',
                token,
            )
            if capture_status not in (200, 201) or capture_data.get('status') != 'COMPLETED':
                return JsonResponse(
                    {'error': 'Payment could not be completed. Please try again.'},
                    status=402,
                )
        except Exception:
            return JsonResponse(
                {'error': 'Payment processing error. Please try again or contact us.'},
                status=500,
            )

        # Payment is captured — write the order. Re-check stock & options defensively under a lock.
        with transaction.atomic():
            product_ids = [item['id'] for item in items]
            locked_products = {
                p.id: p for p in
                Product.objects.select_for_update().filter(id__in=product_ids).prefetch_related('option_groups__values')
            }

            subtotal = 0
            line_items = []
            for item in items:
                product = locked_products.get(item['id'])
                if product:
                    unit_price, options_summary = _resolve_item_options(product, item['option_value_ids'])
                    name = product.name
                else:
                    unit_price, options_summary, name = 0, '', 'Unknown item'
                subtotal += unit_price * item['qty']
                line_items.append((product, name, unit_price, item['qty'], options_summary))

            order = Order.objects.create(
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                shipping_address_line1=address_line1,
                shipping_address_line2=address_line2,
                shipping_city=city,
                shipping_state=state,
                shipping_zip=zip_code,
                subtotal=subtotal,
                total=subtotal,
                status='paid',
                payment_status='paid',
                paypal_order_id=paypal_order_id,
            )

            for product, name, price, qty, options_summary in line_items:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=name,
                    unit_price=price,
                    quantity=qty,
                    selected_options=options_summary,
                )
                if product:
                    product.stock_quantity = max(0, product.stock_quantity - qty)
                    product.save(update_fields=['stock_quantity'])

        try:
            from .email_utils import send_order_emails
            send_order_emails(order)
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'order_number': order.order_number,
            'total': f'{order.total:.2f}',
            'customer_email': order.customer_email,
        })

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
