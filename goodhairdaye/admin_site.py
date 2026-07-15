from datetime import date, timedelta
from django.contrib.admin import AdminSite


class GHDAdminSite(AdminSite):
    site_header = 'Good Hair Daye'
    site_title  = 'GHD Admin'
    index_title = 'Dashboard'

    def index(self, request, extra_context=None):
        from booking.models import Appointment, BlockedDate

        today = date.today()
        extra_context = extra_context or {}
        extra_context['today'] = today
        extra_context['today_appts'] = list(
            Appointment.objects.filter(
                date=today, status__in=['pending', 'confirmed']
            ).order_by('start_time')
        )
        extra_context['upcoming_appts'] = list(
            Appointment.objects.filter(
                date__gt=today,
                date__lte=today + timedelta(days=7),
                status__in=['pending', 'confirmed'],
            ).order_by('date', 'start_time')[:10]
        )
        extra_context['pending_count'] = Appointment.objects.filter(status='pending').count()
        extra_context['week_count'] = Appointment.objects.filter(
            date__gte=today,
            date__lte=today + timedelta(days=7),
            status__in=['pending', 'confirmed'],
        ).count()
        return super().index(request, extra_context)


ghd_admin = GHDAdminSite(name='admin')
