from django import forms

class ContactImportForm(forms.Form):
    file = forms.FileField()
