import json
import calendar
from datetime import date, time, datetime, timedelta

from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from services.models import ServiceCategory, Service
from goodhairdaye.paypal_utils import _paypal_access_token, _paypal_post
from .models import BookingSettings, WorkSchedule, BlockedDate, Appointment


def index(request):
    return render(request, 'booking/index.html')


@require_GET
def api_services(request):
    global_deposit = str(BookingSettings.get().deposit_amount)
    categories = ServiceCategory.objects.prefetch_related('services').order_by('order', 'name')
    data = []
    for cat in categories:
        services = cat.services.filter(is_active=True).order_by('order', 'name')
        if services.exists():
            data.append({
                'category': cat.name,
                'services': [
                    {
                        'id': s.id,
                        'name': s.name,
                        'price': s.price_display,
                        'duration': s.duration,
                        'description': s.description,
                        'deposit': global_deposit,
                        'is_addon': s.is_addon,
                    }
                    for s in services
                ],
            })
    return JsonResponse({'categories': data})


@require_GET
def api_availability(request):
    service_id = request.GET.get('service_id')
    duration_minutes = 30  # default for consultation

    if service_id:
        try:
            svc = Service.objects.get(pk=service_id, is_active=True)
            duration_minutes = svc.duration_minutes
        except Service.DoesNotExist:
            pass

    addon_ids_str = request.GET.get('addon_ids', '')
    if addon_ids_str:
        for aid in addon_ids_str.split(','):
            try:
                addon = Service.objects.get(pk=int(aid.strip()), is_addon=True, is_active=True)
                duration_minutes += addon.duration_minutes
            except (Service.DoesNotExist, ValueError):
                pass

    today = date.today()

    # 18th-of-month rule: before 18th show current month only;
    # on/after 18th also show next month
    _, last_day_current = calendar.monthrange(today.year, today.month)
    next_month_note = None

    if today.day >= 18:
        nm_year = today.year + 1 if today.month == 12 else today.year
        nm_month = 1 if today.month == 12 else today.month + 1
        _, last_day_next = calendar.monthrange(nm_year, nm_month)
        end_date = date(nm_year, nm_month, last_day_next)
    else:
        end_date = date(today.year, today.month, last_day_current)
        nm_opens = date(today.year, today.month, 18)
        next_month_note = (
            f'Bookings for next month open on the 18th of each month. '
            f'Come back on {nm_opens.strftime("%B 18th")} to book for {nm_opens.strftime("%B")}.'
        )

    # Work schedule indexed by day_of_week
    schedules = {ws.day_of_week: ws for ws in WorkSchedule.objects.filter(is_active=True)}

    # Blocked dates in range
    blocked = set(
        BlockedDate.objects.filter(date__gte=today, date__lte=end_date)
        .values_list('date', flat=True)
    )

    # Existing appointments grouped by date
    raw_appts = list(
        Appointment.objects.filter(
            date__gte=today, date__lte=end_date,
            status__in=['pending', 'confirmed']
        ).values('date', 'start_time', 'end_time')
    )
    appts_by_date = {}
    for a in raw_appts:
        appts_by_date.setdefault(a['date'], []).append(a)

    result = []
    current = today
    now = datetime.now()

    while current <= end_date:
        dow = current.weekday()
        if dow in schedules and current not in blocked:
            ws = schedules[dow]
            if ws.start_time and ws.end_time:
                work_start = datetime.combine(current, ws.start_time)
                work_end = datetime.combine(current, ws.end_time)
                day_appts = appts_by_date.get(current, [])

                available = []
                slot_dt = work_start
                while slot_dt + timedelta(minutes=duration_minutes) <= work_end:
                    slot_end = slot_dt + timedelta(minutes=duration_minutes)
                    past = (current == today and slot_dt <= now)
                    conflict = past or any(
                        slot_dt < datetime.combine(current, a['end_time']) and
                        slot_end > datetime.combine(current, a['start_time'])
                        for a in day_appts
                    )
                    if not conflict:
                        available.append({
                            'time': slot_dt.strftime('%H:%M'),
                            'label': slot_dt.strftime('%I:%M %p').lstrip('0'),
                        })
                    slot_dt += timedelta(minutes=30)

                result.append({
                    'date': str(current),
                    'available': available,
                    'fully_booked': len(available) == 0,
                })

        current += timedelta(days=1)

    bk_settings = BookingSettings.get()
    response = {
        'dates': result,
        'same_day_fee': str(bk_settings.same_day_fee),
        'same_day_fee_enabled': bk_settings.same_day_fee_enabled,
        'today': str(today),
        'duration_minutes': duration_minutes,
    }
    if next_month_note:
        response['next_month_note'] = next_month_note

    return JsonResponse(response)


@require_POST
def api_create_paypal_order(request):
    """Create a PayPal order for the deposit amount. Returns {order_id}."""
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_SECRET:
        return JsonResponse({'error': 'Payment is not configured yet. Please contact us to book.'}, status=503)
    try:
        data = json.loads(request.body)
        amount = float(data.get('amount', 0))
        description = data.get('description', 'Hair Appointment Deposit — Good Hair Daye')

        if amount <= 0:
            return JsonResponse({'error': 'Invalid deposit amount.'}, status=400)

        token = _paypal_access_token()
        status_code, order = _paypal_post(
            '/v2/checkout/orders',
            token,
            {
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'amount': {'currency_code': 'USD', 'value': f'{amount:.2f}'},
                    'description': description,
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

        return JsonResponse({'order_id': order['id']})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def api_book(request):
    try:
        data = json.loads(request.body)

        date_str = data.get('date')
        time_str = data.get('start_time')
        service_id = data.get('service_id')
        is_new_client = bool(data.get('is_new_client', False))
        client_name = data.get('client_name', '').strip()
        client_email = data.get('client_email', '').strip()
        client_phone = data.get('client_phone', '').strip()
        cancellation_acknowledged = bool(data.get('cancellation_acknowledged', False))
        notes = data.get('notes', '').strip()
        addon_ids = data.get('addon_ids', [])
        paypal_order_id = data.get('paypal_order_id', '').strip()

        if not all([date_str, time_str, client_name, client_email, client_phone]):
            return JsonResponse({'error': 'Please fill in all required fields.'}, status=400)
        if not cancellation_acknowledged:
            return JsonResponse({'error': 'Please acknowledge the cancellation policy.'}, status=400)
        if not paypal_order_id:
            return JsonResponse({'error': 'Payment is required to complete your booking.'}, status=400)

        try:
            appt_date = date.fromisoformat(date_str)
            appt_time = time.fromisoformat(time_str)
        except ValueError:
            return JsonResponse({'error': 'Invalid date or time.'}, status=400)

        bk_settings = BookingSettings.get()
        service = None
        duration_minutes = 30
        deposit_amount = bk_settings.deposit_amount

        if service_id:
            try:
                service = Service.objects.get(pk=service_id, is_active=True)
                duration_minutes = service.duration_minutes
            except Service.DoesNotExist:
                return JsonResponse({'error': 'Invalid service.'}, status=400)

        addon_names = []
        for aid in addon_ids:
            try:
                addon = Service.objects.get(pk=int(aid), is_addon=True, is_active=True)
                addon_names.append(addon.name)
                duration_minutes += addon.duration_minutes
            except (Service.DoesNotExist, ValueError):
                pass

        start_dt = datetime.combine(appt_date, appt_time)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        end_time = end_dt.time()

        # Double-booking check before capturing payment
        conflicts = Appointment.objects.filter(
            date=appt_date,
            status__in=['pending', 'confirmed'],
            start_time__lt=end_time,
            end_time__gt=appt_time,
        )
        if conflicts.exists():
            return JsonResponse(
                {'error': 'This time slot is no longer available. Please choose another time.'},
                status=409,
            )

        # Capture the PayPal payment — appointment is only created on success
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

        same_day = (appt_date == date.today())
        same_day_fee_applied = same_day and bk_settings.same_day_fee_enabled

        appt = Appointment.objects.create(
            service=service,
            date=appt_date,
            start_time=appt_time,
            end_time=end_time,
            client_name=client_name,
            client_email=client_email,
            client_phone=client_phone,
            is_new_client=is_new_client,
            deposit_amount=deposit_amount,
            same_day_fee_applied=same_day_fee_applied,
            cancellation_acknowledged=cancellation_acknowledged,
            notes=notes,
            addons_display=', '.join(addon_names),
            paypal_order_id=paypal_order_id,
            payment_status='paid',
            status='confirmed',
        )

        try:
            from .email_utils import send_booking_confirmation
            send_booking_confirmation(appt)
        except Exception:
            pass
        try:
            from .sms_utils import send_booking_sms
            send_booking_sms(appt)
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'appointment_id': appt.id,
            'total_deposit': str(appt.total_deposit),
            'same_day_fee_applied': same_day_fee_applied,
            'same_day_fee': str(bk_settings.same_day_fee),
            'service_name': service.name if service else 'Consultation',
            'addons': addon_names,
            'date': appt_date.strftime('%A, %B %d').replace(' 0', ' '),
            'time': appt_time.strftime('%I:%M %p').lstrip('0'),
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
