from django.shortcuts import render

_POLICY_ITEMS = [
    'Manage appointments and provide salon services.',
    'Send booking confirmations, reminders, and service-related communications.',
    'Respond to customer inquiries, reschedule appointments, and provide customer support.',
    'Process payments securely through third-party payment processors.',
    'Send promotions, newsletters, surveys, and marketing communications only when you have opted in.',
    'Operate, maintain, analyze, improve, and secure the website and services.',
    'Comply with applicable legal, tax, and regulatory requirements and enforce our Terms and Conditions.',
]


def privacy(request):
    return render(request, 'pages/privacy/privacy.html', {'policy_items': _POLICY_ITEMS})
