import json

from django.db import models
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from goodhairdaye.admin_common import _staff
import itertools

from shop.models import (
    ProductCategory, Product, ProductOptionGroup, ProductOptionValue,
    ProductImage, ProductVariant, Order,
)


# ── Products & Categories ───────────────────────────────────

@_staff
def shop_products_view(request):
    categories = ProductCategory.objects.prefetch_related(
        models.Prefetch(
            'products',
            queryset=Product.objects.prefetch_related(
                'option_groups__values',
                'gallery_images__option_value',
                'variants__option_values',
            ),
        ),
    ).order_by('order', 'name')

    for cat in categories:
        for product in cat.products.all():
            groups = [
                {
                    'id': g.id, 'name': g.name,
                    'contributes_to_price': g.contributes_to_price,
                    'values': [{'id': v.id, 'label': v.label, 'price_delta': float(v.price_delta)} for v in g.values.all()],
                }
                for g in product.option_groups.all()
            ]
            variants = [
                {
                    'id': variant.id,
                    'value_ids': sorted(v.id for v in variant.option_values.all()),
                    'price': float(variant.price),
                }
                for variant in product.variants.all()
            ]
            photos = [
                {'id': img.id, 'url': img.image.url, 'option_value_id': img.option_value_id}
                for img in product.gallery_images.all()
            ]
            product.admin_payload = {
                'product_id': product.id,
                'base_price': float(product.price),
                'groups': groups,
                'variants': variants,
                'photos': photos,
            }
            product.json_script_id = f'product-meta-{product.id}'

    return render(request, 'ghd_admin/shop_products.html', {'categories': categories})


@_staff
@require_POST
def api_shop_add_category(request):
    data = json.loads(request.body)
    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Category name is required.'}, status=400)
    cat = ProductCategory.objects.create(name=name, order=int(data.get('order', 0)))
    return JsonResponse({'success': True, 'id': cat.id, 'name': cat.name})


@_staff
@require_POST
def api_shop_update_category(request, category_id):
    cat = get_object_or_404(ProductCategory, pk=category_id)
    data = json.loads(request.body)
    if 'name' in data:
        cat.name = data['name'].strip()
    if 'order' in data:
        cat.order = int(data['order'])
    cat.save()
    return JsonResponse({'success': True})


@_staff
@require_POST
def api_shop_delete_category(request, category_id):
    cat = get_object_or_404(ProductCategory, pk=category_id)
    if cat.products.exists():
        return JsonResponse({'error': 'Move or delete the products in this category first.'}, status=400)
    cat.delete()
    return JsonResponse({'success': True})


@_staff
@require_POST
def api_shop_add_product(request):
    category = get_object_or_404(ProductCategory, pk=int(request.POST.get('category_id', 0)))
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Product name is required.'}, status=400)

    product = Product.objects.create(
        category=category,
        name=name,
        description=request.POST.get('description', '').strip(),
        price=request.POST.get('price', 0) or 0,
        stock_quantity=int(request.POST.get('stock_quantity', 0) or 0),
        is_active=request.POST.get('is_active', 'true') == 'true',
    )
    if request.FILES.get('image'):
        file = request.FILES['image']
        ext = file.name.rsplit('.', 1)[-1].lower()
        if ext not in ('jpg', 'jpeg', 'png'):
            product.delete()
            return JsonResponse({'error': 'Only JPG and PNG files are allowed.'}, status=400)
        product.image = file
        product.save()

    return JsonResponse({'success': True, 'id': product.id})


@_staff
@require_POST
def api_shop_update_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if 'category_id' in request.POST and request.POST['category_id']:
        product.category = get_object_or_404(ProductCategory, pk=int(request.POST['category_id']))
    if 'name' in request.POST:
        product.name = request.POST['name'].strip()
    if 'description' in request.POST:
        product.description = request.POST['description'].strip()
    if 'price' in request.POST:
        product.price = request.POST['price']
    if 'stock_quantity' in request.POST:
        product.stock_quantity = int(request.POST['stock_quantity'])
    if 'is_active' in request.POST:
        product.is_active = request.POST['is_active'] == 'true'

    if request.FILES.get('image'):
        file = request.FILES['image']
        ext = file.name.rsplit('.', 1)[-1].lower()
        if ext not in ('jpg', 'jpeg', 'png'):
            return JsonResponse({'error': 'Only JPG and PNG files are allowed.'}, status=400)
        if product.image:
            product.image.delete(save=False)
        product.image = file

    product.save()
    return JsonResponse({'success': True, 'image_url': product.image.url if product.image else None})


@_staff
@require_POST
def api_shop_delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if product.image:
        product.image.delete(save=False)
    product.delete()
    return JsonResponse({'success': True})


# ── Product Options ──────────────────────────────────────────

@_staff
@require_POST
def api_shop_add_option_group(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    data = json.loads(request.body)
    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Option group name is required.'}, status=400)
    group = ProductOptionGroup.objects.create(product=product, name=name, order=int(data.get('order', 0)))
    return JsonResponse({'success': True, 'id': group.id, 'name': group.name})


@_staff
@require_POST
def api_shop_update_option_group(request, group_id):
    group = get_object_or_404(ProductOptionGroup, pk=group_id)
    data = json.loads(request.body)
    if 'name' in data:
        group.name = data['name'].strip()
    if 'order' in data:
        group.order = int(data['order'])
    if 'contributes_to_price' in data:
        group.contributes_to_price = bool(data['contributes_to_price'])
    group.save()
    return JsonResponse({'success': True})


@_staff
@require_POST
def api_shop_delete_option_group(request, group_id):
    group = get_object_or_404(ProductOptionGroup, pk=group_id)
    group.delete()
    return JsonResponse({'success': True})


@_staff
@require_POST
def api_shop_add_option_value(request, group_id):
    group = get_object_or_404(ProductOptionGroup, pk=group_id)
    data = json.loads(request.body)
    label = data.get('label', '').strip()
    if not label:
        return JsonResponse({'error': 'Option value label is required.'}, status=400)
    value = ProductOptionValue.objects.create(
        group=group,
        label=label,
        price_delta=data.get('price_delta', 0) or 0,
        order=int(data.get('order', 0)),
    )
    return JsonResponse({'success': True, 'id': value.id, 'label': value.label, 'price_delta': float(value.price_delta)})


@_staff
@require_POST
def api_shop_update_option_value(request, value_id):
    value = get_object_or_404(ProductOptionValue, pk=value_id)
    data = json.loads(request.body)
    if 'label' in data:
        value.label = data['label'].strip()
    if 'price_delta' in data:
        value.price_delta = data['price_delta'] or 0
    if 'order' in data:
        value.order = int(data['order'])
    value.save()
    return JsonResponse({'success': True})


@_staff
@require_POST
def api_shop_delete_option_value(request, value_id):
    value = get_object_or_404(ProductOptionValue, pk=value_id)
    value.delete()
    return JsonResponse({'success': True})


# ── Product Variants (combination-specific pricing) ──────────

@_staff
@require_POST
def api_shop_set_variant(request, product_id):
    """Create, update, or delete a combination-specific price.
    body: {option_value_ids: [...], price: float_or_null}
    Passing price=null deletes the variant for that combination."""
    product = get_object_or_404(Product, pk=product_id)
    data = json.loads(request.body)
    value_ids = data.get('option_value_ids') or []
    price = data.get('price')

    values = list(ProductOptionValue.objects.filter(id__in=value_ids, group__product=product))
    if len(values) != len(value_ids):
        return JsonResponse({'error': 'Invalid option selection.'}, status=400)

    target_ids = frozenset(value_ids)

    # Find existing variant matching exactly this combination
    existing = None
    for variant in product.variants.prefetch_related('option_values').all():
        if frozenset(v.id for v in variant.option_values.all()) == target_ids:
            existing = variant
            break

    if price is None:
        if existing:
            existing.delete()
        return JsonResponse({'success': True, 'deleted': True})

    if existing:
        existing.price = price
        existing.save()
        vid = existing.id
    else:
        new_variant = ProductVariant.objects.create(product=product, price=price)
        new_variant.option_values.set(values)
        vid = new_variant.id

    return JsonResponse({'success': True, 'id': vid})


# ── Product Photos ───────────────────────────────────────────

@_staff
@require_POST
def api_shop_add_image(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    file = request.FILES.get('image')
    if not file:
        return JsonResponse({'error': 'An image file is required.'}, status=400)
    ext = file.name.rsplit('.', 1)[-1].lower()
    if ext not in ('jpg', 'jpeg', 'png'):
        return JsonResponse({'error': 'Only JPG and PNG files are allowed.'}, status=400)

    option_value = None
    option_value_id = request.POST.get('option_value_id')
    if option_value_id:
        option_value = get_object_or_404(ProductOptionValue, pk=option_value_id, group__product=product)

    img = ProductImage.objects.create(
        product=product,
        image=file,
        option_value=option_value,
        order=int(request.POST.get('order', 0) or 0),
    )
    return JsonResponse({'success': True, 'id': img.id, 'url': img.image.url})


@_staff
@require_POST
def api_shop_update_image(request, image_id):
    img = get_object_or_404(ProductImage, pk=image_id)
    data = json.loads(request.body)
    if 'option_value_id' in data:
        val = data['option_value_id']
        if val:
            img.option_value = get_object_or_404(ProductOptionValue, pk=val, group__product=img.product)
        else:
            img.option_value = None
    if 'order' in data:
        img.order = int(data['order'])
    img.save()
    return JsonResponse({'success': True})


@_staff
@require_POST
def api_shop_delete_image(request, image_id):
    img = get_object_or_404(ProductImage, pk=image_id)
    img.image.delete(save=False)
    img.delete()
    return JsonResponse({'success': True})


# ── Orders ───────────────────────────────────────────────────

@_staff
def shop_orders_view(request):
    status = request.GET.get('filter', 'all')
    qs = Order.objects.prefetch_related('items').all()
    if status != 'all':
        qs = qs.filter(status=status)
    return render(request, 'ghd_admin/shop_orders.html', {'orders': qs, 'filter': status})


@_staff
@require_POST
def api_order_update_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    data = json.loads(request.body)
    new_status = data.get('status')
    if new_status not in dict(Order.STATUS_CHOICES):
        return JsonResponse({'error': 'Invalid status.'}, status=400)

    previous_status = order.status

    if new_status == 'cancelled' and previous_status != 'cancelled' and not order.stock_restored:
        for item in order.items.select_related('product'):
            if item.product:
                item.product.stock_quantity = models.F('stock_quantity') + item.quantity
                item.product.save(update_fields=['stock_quantity'])
        order.stock_restored = True

    order.status = new_status
    order.save()

    if new_status != previous_status and data.get('notify_customer', True):
        try:
            from shop.email_utils import send_status_update_email
            send_status_update_email(order)
        except Exception:
            pass

    return JsonResponse({'success': True})
