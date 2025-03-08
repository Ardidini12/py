from celery import shared_task
from .models import Contact, BirthdayMessage, SendSettings
import pywhatkit
from datetime import datetime, timedelta
from django.utils import timezone
import time
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_birthday_messages():
    settings = SendSettings.objects.first()
    today = datetime.now().date()
    
    # Get today's birthdays
    birthdays = Contact.objects.filter(birthday__month=today.month, birthday__day=today.day)
    
    # Schedule messages
    current_time = datetime.combine(today, datetime.min.time()).replace(hour=settings.start_hour)
    
    for contact in birthdays:
        BirthdayMessage.objects.create(
            recipient=contact,
            message=f"Happy Birthday {contact.name}! 🎉",
            scheduled_time=current_time
        )
        current_time += timedelta(minutes=settings.interval_minutes)
    
    # Start sending process
    send_scheduled_messages.delay()

@shared_task
def send_scheduled_messages():
    settings = SendSettings.objects.first()
    if not settings:
        return  # No settings configured
    
    messages = BirthdayMessage.objects.filter(
        sent=False, 
        scheduled_time__lte=timezone.now()
    ).select_related('recipient')
    
    try:
        # Browser session management
        if not settings.browser_tab_id:
            pywhatkit.start_client()
            settings.browser_tab_id = pywhatkit.get_active_session()
            settings.save()

        # Send messages with rate limiting
        for index, message in enumerate(messages):
            try:
                pywhatkit.sendwhatmsg_instanced(
                    session=settings.browser_tab_id,
                    phone_no=message.recipient.phone_number,
                    message=message.message,
                    time_hour=message.scheduled_time.hour,
                    time_min=message.scheduled_time.minute,
                    tab_close=True,
                    close_time=3
                )
                message.sent = True
                message.sent_at = timezone.now()
                message.save()
                
                # Rate limiting between messages
                if index < len(messages) - 1:
                    time.sleep(settings.interval_minutes * 60)
                    
            except Exception as e:
                logger.error(f"Failed to send to {message.recipient}: {str(e)}")
                continue
                
    finally:
        # Clean up browser session
        if settings.browser_tab_id:
            pywhatkit.close_tab(settings.browser_tab_id)
            settings.browser_tab_id = ''
            settings.save()