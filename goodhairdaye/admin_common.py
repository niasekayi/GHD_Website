from django.contrib.admin.views.decorators import staff_member_required

LOGIN_URL = '/admin/login/'


def _staff(view):
    return staff_member_required(view, login_url=LOGIN_URL)
