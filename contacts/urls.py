from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    path('import/', views.import_contacts, name='import_contacts'),
    path('export/', views.export_contacts, name='export_contacts'),
]
