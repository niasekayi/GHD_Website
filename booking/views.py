import json
import calendar
from datetime import date, time, datetime, timedelta

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from services.models import ServiceCategory, Service
from .models import BookingSettings, WorkSchedule, BlockedDate, Appointment


def index(request):
    return render(request, 'booking/index.html')


@require_GET
def api_services(request):
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
                        'deposit': str(s.deposit_amount),
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
            f'Bookings for next month open on {nm_opens.strftime("%B 18th")}. '
            f'Please come back after that date to book for the next month.'
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
                    conflict = any(
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

    settings = BookingSettings.get()
    response = {
        'dates': result,
        'same_day_fee': str(settings.same_day_fee),
        'same_day_fee_enabled': settings.same_day_fee_enabled,
        'today': str(today),
        'duration_minutes': duration_minutes,
    }
    if next_month_note:
        response['next_month_note'] = next_month_note

    return JsonResponse(response)


@require_POST
def api_book(request):
    try:
        data = json.loads(request.body)

        date_str = data.get('date')
        time_str = data.get('start_time')  # "HH:MM"
        service_id = data.get('service_id')
        is_new_client = bool(data.get('is_new_client', False))
        client_name = data.get('client_name', '').strip()
        client_email = data.get('client_email', '').strip()
        client_phone = data.get('client_phone', '').strip()
        cancellation_acknowledged = bool(data.get('cancellation_acknowledged', False))
        notes = data.get('notes', '').strip()
        addon_ids = data.get('addon_ids', [])

        if not all([date_str, time_str, client_name, client_email, client_phone]):
            return JsonResponse({'error': 'Please fill in all required fields.'}, status=400)
        if not cancellation_acknowledged:
            return JsonResponse({'error': 'Please acknowledge the cancellation policy.'}, status=400)

        try:
            appt_date = date.fromisoformat(date_str)
            appt_time = time.fromisoformat(time_str)
        except ValueError:
            return JsonResponse({'error': 'Invalid date or time.'}, status=400)

        service = None
        duration_minutes = 30
        deposit_amount = 40  # consultation fee

        if service_id:
            try:
                service = Service.objects.get(pk=service_id, is_active=True)
                duration_minutes = service.duration_minutes
                deposit_amount = service.deposit_amount
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

        # Double-booking protection: check for overlapping confirmed/pending appointments
        conflicts = Appointment.objects.filter(
            date=appt_date,
            status__in=['pending', 'confirmed'],
            start_time__lt=end_time,
            end_time__gt=appt_time,
        )
        if conflicts.exists():
            return JsonResponse(
                {'error': 'This time slot is no longer available. Please choose another time.'},
                status=409
            )

        settings = BookingSettings.get()
        same_day = (appt_date == date.today())
        same_day_fee_applied = same_day and settings.same_day_fee_enabled

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
        )

        # Send confirmation emails and SMS (non-blocking; fail_silently=True)
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
            'same_day_fee': str(settings.same_day_fee),
            'service_name': service.name if service else 'Consultation',
            'addons': addon_names,
            'date': appt_date.strftime('%A, %B %d').replace(' 0', ' '),
            'time': appt_time.strftime('%I:%M %p').lstrip('0'),
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
