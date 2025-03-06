from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Contact

class ContactResource(resources.ModelResource):
    class Meta:
        model = Contact
        import_id_fields = ('phone_number',)  # Assuming phone_number is unique
        fields = ('name', 'surname', 'phone_number', 'email', 'birthday', 'source')

@admin.register(Contact)
class ContactAdmin(ImportExportModelAdmin):
    resource_class = ContactResource
    list_display = ('name', 'surname', 'phone_number', 'email', 'birthday', 'source')

    def save_model(self, request, obj, form, change):
        # Set source to 'Manually added' only when creating new through admin
        if not change:
            obj.source = 'Manually added'
        super().save_model(request, obj, form, change)
