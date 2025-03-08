from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from .models import Contact, SendSettings
from django.utils import timezone

@staff_member_required
def birthday_dashboard(request):
    today = timezone.now().date()
    context = {
        'today_birthdays': Contact.objects.filter(
            birthday__month=today.month,
            birthday__day=today.day
        ),
        'has_permission': True
    }
    
    if request.method == 'POST':
        start_hour = int(request.POST.get('start_hour', 9))
        settings, _ = SendSettings.objects.get_or_create()
        settings.start_hour = start_hour
        settings.save()
    
    return render(request, 'admin/birthdays.html', context) 