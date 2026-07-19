import json
import calendar as cal_module
from datetime import date, timedelta, time as dt_time

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from django.db import models
from booking.models import WorkSchedule, BlockedDate, Appointment, BookingSettings
from services.models import ServiceCategory, Service
from pages.models import GalleryPhoto, Review
from goodhairdaye.admin_common import _staff, LOGIN_URL


@_staff
def dashboard(request):
    today = date.today()
    today_count   = Appointment.objects.filter(date=today, status__in=['pending', 'confirmed']).count()
    week_count    = Appointment.objects.filter(date__gte=today, date__lte=today + timedelta(days=7), status__in=['pending', 'confirmed']).count()
    pending_count = Appointment.objects.filter(status='pending').count()

    return render(request, 'ghd_admin/dashboard.html', {
        'today': today,
        'today_appts': Appointment.objects.filter(
            date=today, status__in=['pending', 'confirmed']
        ).order_by('start_time'),
        'upcoming': Appointment.objects.filter(
            date__gt=today,
            date__lte=today + timedelta(days=7),
            status__in=['pending', 'confirmed'],
        ).order_by('date', 'start_time')[:8],
        'pending_count': pending_count,
        'week_count':    week_count,
        'stats': [
            ('Today', today_count,   '/admin/appointments/?filter=today'),
            ('This Week', week_count, '/admin/appointments/'),
            ('Pending', pending_count, '/admin/appointments/?filter=all'),
        ],
    })


@_staff
def services_view(request):
    categories = ServiceCategory.objects.prefetch_related(
        models.Prefetch('services', queryset=Service.objects.filter(is_addon=False))
    ).order_by('order', 'name')
    addons = Service.objects.filter(is_addon=True).select_related('category').order_by('category__order', 'name')
    booking_settings = BookingSettings.get()
    return render(request, 'ghd_admin/services.html', {
        'categories': categories,
        'addons': addons,
        'booking_settings': booking_settings,
    })


@_staff
def availability_view(request):
    today = date.today()
    year  = int(request.GET.get('year',  today.year))
    month = int(request.GET.get('month', today.month))

    # Clamp to current month minimum
    if date(year, month, 1) < date(today.year, today.month, 1):
        year, month = today.year, today.month

    _, days_in_month = cal_module.monthrange(year, month)
    first_dow = date(year, month, 1).weekday()  # Mon=0

    blocked_dates = set(
        BlockedDate.objects.filter(date__year=year, date__month=month)
        .values_list('date', flat=True)
    )
    schedules = {ws.day_of_week: ws for ws in WorkSchedule.objects.all()}
    appts_by_date = {}
    for a in Appointment.objects.filter(
        date__year=year, date__month=month, status__in=['pending', 'confirmed']
    ):
        appts_by_date.setdefault(a.date, []).append(a)

    days = []
    for d in range(1, days_in_month + 1):
        day_date = date(year, month, d)
        dow = day_date.weekday()
        ws  = schedules.get(dow)
        days.append({
            'date':       day_date,
            'day':        d,
            'dow':        dow,
            'is_working': bool(ws and ws.is_active and ws.start_time),
            'is_blocked': day_date in blocked_dates,
            'is_past':    day_date < today,
            'is_today':   day_date == today,
            'appt_count': len(appts_by_date.get(day_date, [])),
        })

    prev_month = month - 1 or 12
    prev_year  = year - (1 if month == 1 else 0)
    next_month = (month % 12) + 1
    next_year  = year + (1 if month == 12 else 0)

    DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    schedule_rows = []
    for dow, name in enumerate(DAY_NAMES):
        ws = schedules.get(dow)
        schedule_rows.append({
            'dow':       dow,
            'name':      name,
            'is_active': bool(ws and ws.is_active),
            'start':     ws.start_time.strftime('%H:%M') if ws and ws.start_time else '09:00',
            'end':       ws.end_time.strftime('%H:%M') if ws and ws.end_time else '17:00',
        })

    return render(request, 'ghd_admin/availability.html', {
        'year':            year,
        'month':           month,
        'month_name':      date(year, month, 1).strftime('%B %Y'),
        'days':            days,
        'start_pad_range': range(first_dow),
        'day_names':       DAY_NAMES,
        'schedule_rows':   schedule_rows,
        'prev_year':       prev_year,
        'prev_month':      prev_month,
        'next_year':       next_year,
        'next_month':      next_month,
        'can_go_prev':     date(prev_year, prev_month, 1) >= date(today.year, today.month, 1),
        'today':           today,
    })


@_staff
def appointments_view(request):
    today  = date.today()
    status = request.GET.get('filter', 'upcoming')

    qs = Appointment.objects.select_related('service')
    if status == 'today':
        qs = qs.filter(date=today)
    elif status == 'past':
        qs = qs.filter(date__lt=today).order_by('-date', '-start_time')
    elif status == 'all':
        qs = qs.order_by('-date', '-start_time')
    else:
        qs = qs.filter(date__gte=today, status__in=['pending', 'confirmed']).order_by('date', 'start_time')

    return render(request, 'ghd_admin/appointments.html', {
        'appointments': qs,
        'filter':       status,
        'today':        today,
    })


# ── AJAX ────────────────────────────────────────────────────

@_staff
@require_POST
def api_toggle_date(request):
    data = json.loads(request.body)
    try:
        d = date.fromisoformat(data.get('date', ''))
    except ValueError:
        return JsonResponse({'error': 'Invalid date.'}, status=400)
    if d < date.today():
        return JsonResponse({'error': 'Cannot edit past dates.'}, status=400)
    obj, created = BlockedDate.objects.get_or_create(date=d)
    if not created:
        obj.delete()
        return JsonResponse({'blocked': False})
    return JsonResponse({'blocked': True})


@_staff
@require_POST
def api_update_schedule(request):
    data      = json.loads(request.body)
    dow       = int(data['dow'])
    is_active = bool(data.get('is_active', True))
    ws, _     = WorkSchedule.objects.get_or_create(day_of_week=dow)
    ws.is_active = is_active
    if data.get('start_time'):
        h, m = map(int, data['start_time'].split(':'))
        ws.start_time = dt_time(h, m)
    if data.get('end_time'):
        h, m = map(int, data['end_time'].split(':'))
        ws.end_time = dt_time(h, m)
    ws.save()
    return JsonResponse({'success': True})


@_staff
@require_POST
def api_update_service(request, service_id):
    data = json.loads(request.body)
    svc  = get_object_or_404(Service, pk=service_id)
    for field in ('name', 'price_display', 'duration', 'description'):
        if field in data:
            setattr(svc, field, data[field].strip())
    if 'deposit_amount' in data:
        svc.deposit_amount = float(data['deposit_amount'])
    if 'is_active' in data:
        svc.is_active = bool(data['is_active'])
    if 'is_addon' in data:
        svc.is_addon = bool(data['is_addon'])
    svc.save()
    return JsonResponse({'success': True})


@_staff
@require_POST
def api_add_service(request):
    data     = json.loads(request.body)
    category = get_object_or_404(ServiceCategory, pk=int(data['category_id']))
    global_deposit = float(BookingSettings.get().deposit_amount)
    svc = Service.objects.create(
        category=category,
        name=data.get('name', '').strip(),
        price_display=data.get('price_display', '').strip(),
        duration=data.get('duration', '60 min').strip(),
        description=data.get('description', '').strip(),
        deposit_amount=float(data.get('deposit_amount', global_deposit)),
        is_active=True,
        is_addon=bool(data.get('is_addon', False)),
    )
    return JsonResponse({'success': True, 'id': svc.id})


@_staff
@require_POST
def api_delete_service(request, service_id):
    svc = get_object_or_404(Service, pk=service_id)
    svc.delete()
    return JsonResponse({'success': True})


@_staff
@require_POST
def api_update_booking_settings(request):
    data = json.loads(request.body)
    bk = BookingSettings.get()
    if 'deposit_amount' in data:
        bk.deposit_amount = float(data['deposit_amount'])
    bk.save()
    return JsonResponse({'success': True})


@_staff
@require_POST
def api_add_category(request):
    data = json.loads(request.body)
    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Category name is required.'}, status=400)
    if ServiceCategory.objects.filter(name=name).exists():
        return JsonResponse({'error': 'A category with this name already exists.'}, status=400)
    cat = ServiceCategory.objects.create(name=name, order=ServiceCategory.objects.count())
    return JsonResponse({'success': True, 'id': cat.id, 'name': cat.name})


@_staff
@require_POST
def api_delete_category(request, cat_id):
    cat = get_object_or_404(ServiceCategory, pk=cat_id)
    service_count = cat.services.count()
    if service_count > 0:
        return JsonResponse(
            {'error': f'"{cat.name}" still has {service_count} service(s). Move or delete them first.'},
            status=400,
        )
    cat.delete()
    return JsonResponse({'success': True})


@_staff
def users_view(request):
    users = User.objects.filter(is_staff=True).order_by('username')
    return render(request, 'ghd_admin/users.html', {'staff_users': users})


@_staff
@require_POST
def api_add_user(request):
    data     = json.loads(request.body)
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    name     = data.get('name', '').strip()
    if not username or not password:
        return JsonResponse({'error': 'Username and password are required.'}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'Username already taken.'}, status=400)
    try:
        validate_password(password)
    except ValidationError as e:
        return JsonResponse({'error': ' '.join(e.messages)}, status=400)
    first, _, last = name.partition(' ')
    user = User.objects.create_user(
        username=username, password=password,
        first_name=first, last_name=last,
        is_staff=True,
    )
    return JsonResponse({'success': True, 'id': user.id, 'username': user.username})


@_staff
@require_POST
def api_delete_user(request, user_id):
    if request.user.id == user_id:
        return JsonResponse({'error': 'You cannot delete your own account.'}, status=400)
    user = get_object_or_404(User, pk=user_id, is_staff=True)
    user.delete()
    return JsonResponse({'success': True})


@_staff
@require_POST
def api_update_appointment(request, appt_id):
    data = json.loads(request.body)
    appt = get_object_or_404(Appointment, pk=appt_id)
    if 'status' in data:
        appt.status = data['status']
    if 'notes' in data:
        appt.notes = data['notes']
    appt.save()
    return JsonResponse({'success': True})


# ── Gallery ─────────────────────────────────────────────────

@_staff
def gallery_view(request):
    photos = GalleryPhoto.objects.select_related('service').all()
    services = Service.objects.filter(is_active=True, is_addon=False).select_related('category').order_by('category__order', 'name')
    return render(request, 'ghd_admin/gallery.html', {'photos': photos, 'services': services})


@_staff
@require_POST
def api_gallery_add(request):
    file = request.FILES.get('image')
    if not file:
        return JsonResponse({'error': 'No image provided.'}, status=400)
    ext = file.name.rsplit('.', 1)[-1].lower()
    if ext not in ('jpg', 'jpeg', 'png'):
        return JsonResponse({'error': 'Only JPG and PNG files are allowed.'}, status=400)
    service_id = request.POST.get('service_id') or None
    service = None
    if service_id:
        try:
            service = Service.objects.get(pk=int(service_id))
        except (Service.DoesNotExist, ValueError):
            pass
    photo = GalleryPhoto.objects.create(
        image=file,
        caption=request.POST.get('caption', '').strip(),
        service=service,
        order=int(request.POST.get('order', 0)),
        is_active=request.POST.get('is_active', 'true') == 'true',
    )
    return JsonResponse({'success': True, 'id': photo.id, 'url': photo.image.url})


@_staff
@require_POST
def api_gallery_update(request, photo_id):
    photo = get_object_or_404(GalleryPhoto, pk=photo_id)
    if request.FILES.get('image'):
        file = request.FILES['image']
        ext = file.name.rsplit('.', 1)[-1].lower()
        if ext not in ('jpg', 'jpeg', 'png'):
            return JsonResponse({'error': 'Only JPG and PNG files are allowed.'}, status=400)
        photo.image = file
    if 'caption' in request.POST:
        photo.caption = request.POST['caption'].strip()
    if 'order' in request.POST:
        photo.order = int(request.POST['order'])
    if 'is_active' in request.POST:
        photo.is_active = request.POST['is_active'] == 'true'
    if 'service_id' in request.POST:
        sid = request.POST['service_id']
        if sid:
            try:
                photo.service = Service.objects.get(pk=int(sid))
            except (Service.DoesNotExist, ValueError):
                photo.service = None
        else:
            photo.service = None
    photo.save()
    return JsonResponse({'success': True, 'url': photo.image.url})


@_staff
@require_POST
def api_gallery_delete(request, photo_id):
    photo = get_object_or_404(GalleryPhoto, pk=photo_id)
    photo.image.delete(save=False)
    photo.delete()
    return JsonResponse({'success': True})


# ── Reviews ─────────────────────────────────────────────────

@_staff
def reviews_view(request):
    reviews = Review.objects.all()
    return render(request, 'ghd_admin/reviews.html', {'reviews': reviews})


@_staff
@require_POST
def api_review_add(request):
    name = request.POST.get('client_name', '').strip()
    body = request.POST.get('body', '').strip()
    if not name or not body:
        return JsonResponse({'error': 'Name and review text are required.'}, status=400)
    review = Review.objects.create(
        client_name=name,
        rating=int(request.POST.get('rating', 5)),
        body=body,
        video_url=request.POST.get('video_url', '').strip(),
        order=int(request.POST.get('order', 0)),
        is_active=request.POST.get('is_active', 'true') == 'true',
    )
    if request.FILES.get('photo'):
        review.photo = request.FILES['photo']
        review.save()
    return JsonResponse({'success': True, 'id': review.id})


@_staff
@require_POST
def api_review_update(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if 'client_name' in request.POST:
        review.client_name = request.POST['client_name'].strip()
    if 'body' in request.POST:
        review.body = request.POST['body'].strip()
    if 'rating' in request.POST:
        review.rating = int(request.POST['rating'])
    if 'video_url' in request.POST:
        review.video_url = request.POST['video_url'].strip()
    if 'order' in request.POST:
        review.order = int(request.POST['order'])
    if 'is_active' in request.POST:
        review.is_active = request.POST['is_active'] == 'true'
    if request.FILES.get('photo'):
        if review.photo:
            review.photo.delete(save=False)
        review.photo = request.FILES['photo']
    review.save()
    return JsonResponse({'success': True})


@_staff
@require_POST
def api_review_delete(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if review.photo:
        review.photo.delete(save=False)
    review.delete()
    return JsonResponse({'success': True})
