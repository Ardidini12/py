from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Contact

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
