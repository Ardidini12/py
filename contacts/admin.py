from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Contact, BirthdayMessage, SendSettings
import pywhatkit
from django.utils import timezone
from django.urls import path
from .admin_views import birthday_dashboard

class ContactResource(resources.ModelResource):
    def before_import_row(self, row, **kwargs):
        # Set source from filename during imports
        row['source'] = f'Imported from "{kwargs["file_name"]}"'
    
    class Meta:
        model = Contact
        import_id_fields = ('phone_number',)
        fields = ('name', 'surname', 'phone_number', 'email', 'birthday', 'source')

@admin.register(Contact)
class ContactAdmin(ImportExportModelAdmin):
    resource_class = ContactResource
    list_display = ('name', 'surname', 'phone_number', 'email', 'birthday', 'source')

    def save_model(self, request, obj, form, change):
        # Only set source for manual additions (not imports)
        if not change and not obj.source:
            obj.source = 'Manually added'
        super().save_model(request, obj, form, change)

@admin.register(BirthdayMessage)
class BirthdayMessageAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'scheduled_time', 'sent', 'countdown')
    
    def countdown(self, obj):
        if not obj.sent:
            delta = obj.scheduled_time - timezone.now()
            return f"{delta.seconds//3600} hours { (delta.seconds//60)%60} minutes left"
        return "Sent"
    countdown.short_description = 'Time Remaining'

@admin.register(SendSettings)
class SendSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SendSettings.objects.exists()
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('birthdays/', self.admin_site.admin_view(birthday_dashboard), name='birthday-dashboard'),
        ]
        return custom_urls + urls
