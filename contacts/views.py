from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Contact
from .forms import ContactImportForm
import pandas as pd
from django.http import HttpResponse
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.utils import IntegrityError

# Create your views here.

def import_contacts(request):
    if request.method == 'POST':
        if 'confirm_import' in request.POST:
            return handle_confirmed_import(request)
            
        form = ContactImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = form.cleaned_data['file']
                file_name = file.name
                df = read_file(file)
                
                contacts_data, invalid_entries = process_contacts(df, file_name)
                
                if invalid_entries:
                    request.session['import_data'] = contacts_data
                    request.session['invalid_entries'] = invalid_entries
                    request.session['import_file_name'] = file_name
                    return render(request, 'contacts/import_preview.html', {
                        'invalid_entries': invalid_entries,
                        'file_name': file_name
                    })
                
                return finalize_import(request, contacts_data, file_name)
                
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
    else:
        form = ContactImportForm()
    return render(request, 'contacts/import_contacts.html', {'form': form})

def export_contacts(request):
    contacts = Contact.objects.all()
    df = pd.DataFrame(list(contacts.values()))
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="contacts.csv"'
    df.to_csv(path_or_buf=response, index=False)
    return response

# Helper functions
def read_file(file):
    file_name = file.name
    if file_name.endswith('.csv'):
        return pd.read_csv(file)
    elif file_name.endswith('.xlsx'):
        return pd.read_excel(file, engine='openpyxl')
    elif file_name.endswith('.json'):
        return pd.read_json(file)
    raise ValueError("Unsupported file format")

def process_contacts(df, file_name):
    contacts_data = []
    invalid_entries = []
    
    for index, row in df.iterrows():
        phone = str(row.get('phone_number', '')).strip()
        entry = {
            'name': row.get('name', ''),
            'surname': row.get('surname', ''),
            'phone': phone,
            'email': row.get('email', ''),
            'birthday': row.get('birthday', ''),
            'row_num': index + 2,
            'errors': [],
            'original_data': row.to_dict()
        }
        
        # Validate phone
        if not phone.startswith('+'):
            entry['errors'].append('Missing country code')
        if not phone[1:].isdigit():
            entry['errors'].append('Invalid characters in phone number')
            
        if entry['errors']:
            invalid_entries.append(entry)
        else:
            contacts_data.append({
                'name': row['name'],
                'surname': row['surname'],
                'phone_number': phone,  # Use original phone value
                'email': row.get('email'),
                'birthday': row['birthday'],
                'source': f"Imported from '{file_name}'"  # Set source here
            })
    
    return contacts_data, invalid_entries

def handle_confirmed_import(request):
    file_name = request.session.get('import_file_name')
    contacts_data = request.session.get('import_data', [])
    invalid_entries = request.session.get('invalid_entries', [])
    updates = {}

    # Collect phone number updates from the form
    for entry in invalid_entries:
        key = f"phone_{entry['row_num']}"
        updates[entry['row_num']] = request.POST.get(key, entry['phone']).strip()

    valid_count = 0
    errors = []
    
    try:
        # Process original valid entries
        for data in contacts_data:
            phone_number = data['phone_number'].strip()
            try:
                contact, created = Contact.objects.get_or_create(
                    phone_number=phone_number,
                    defaults={
                        'name': data['name'],
                        'surname': data['surname'],
                        'email': data.get('email'),
                        'birthday': data['birthday'],
                        'source': f"Imported from '{file_name}'"
                    }
                )
                if not created:
                    # Update existing contact including source
                    contact.name = data['name']
                    contact.surname = data['surname']
                    contact.email = data.get('email')
                    contact.birthday = data['birthday']
                    contact.source = f"Updated from '{file_name}'"
                    contact.save()
                valid_count += 1
            except IntegrityError:
                errors.append(f"Duplicate number {phone_number} in row {data.get('row_num', '?')}")

        # Process corrected invalid entries
        for entry in invalid_entries:
            corrected_phone = updates.get(entry['row_num'], entry['phone']).strip()
            
            # Validate corrected phone
            validation_errors = []
            if not corrected_phone.startswith('+'):
                validation_errors.append('Missing country code')
            if not corrected_phone[1:].isdigit():
                validation_errors.append('Invalid characters')
            
            if validation_errors:
                errors.append(f"Row {entry['row_num']}: {', '.join(validation_errors)}")
                continue

            try:
                contact, created = Contact.objects.get_or_create(
                    phone_number=corrected_phone,
                    defaults={
                        'name': entry['name'],
                        'surname': entry['surname'],
                        'email': entry.get('email'),
                        'birthday': entry['birthday'],
                        'source': f"Imported from '{file_name}'"
                    }
                )
                if not created:
                    contact.source = f"Updated from '{file_name}'"
                    contact.save()
                valid_count += 1
            except IntegrityError:
                errors.append(f"Duplicate number {corrected_phone} in row {entry['row_num']}")

        if errors:
            messages.warning(request, f"Imported {valid_count} contacts with remaining errors: {'; '.join(errors)}")
        else:
            messages.success(request, f"Successfully imported {valid_count} contacts")

    except Exception as e:
        messages.error(request, f"Import failed: {str(e)}")
    finally:
        # Clear session data
        for key in ['import_data', 'invalid_entries', 'import_file_name']:
            if key in request.session:
                del request.session[key]
    
    return redirect('contacts:import_contacts')

def finalize_import(request, contacts_data, file_name):
    try:
        for data in contacts_data:
            phone_number = data['phone_number'].strip()
            try:
                Contact.objects.get_or_create(
                    phone_number=phone_number,
                    defaults={
                        'name': data['name'],
                        'surname': data['surname'],
                        'email': data.get('email'),
                        'birthday': data['birthday'],
                        'source': f"Imported from '{file_name}'"
                    }
                )
            except IntegrityError:
                messages.error(request, f"Duplicate number {phone_number} found and skipped")
        messages.success(request, f"Successfully imported {len(contacts_data)} contacts")
    except Exception as e:
        messages.error(request, f"Import failed: {str(e)}")
    return redirect('contacts:import_contacts')
