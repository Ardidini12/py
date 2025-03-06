from import_export import resources
from .models import Contact

class ContactResource(resources.ModelResource):
    def before_import_row(self, row, **kwargs):
        row['source'] = f'Imported from "{kwargs["file_name"]}"'
    
    class Meta:
        model = Contact
        fields = ('id', 'name', 'phone_number', 'email', 'source')
        import_id_fields = ['id'] 