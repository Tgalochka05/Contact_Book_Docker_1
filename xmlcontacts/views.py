import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.http import FileResponse, Http404
from django.conf import settings
from django.contrib import messages
from django.db import models
import json
from django.core import serializers
from .forms import ContactForm, UploadXMLForm, ContactEditForm, DataSourceForm
from .models import Contact
from .utils import (
    save_contact_to_xml, get_all_contacts_from_xml,
    validate_xml_file, get_contacts_from_uploaded_xml,
    get_all_xml_files, generate_xml_filename, ensure_contacts_dir, 
    get_contacts_xml_dir, save_contact_to_db, search_contacts_in_db, get_all_contacts_from_db
)

# Форма для ввода контакта
def contact_form(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_data = form.cleaned_data
            save_to = contact_data.pop('save_to')  # Убираем поле выбора
            
            if save_to == 'db':
                # Сохраняем в базу данных
                success, message = save_contact_to_db(contact_data)
                if success:
                    messages.success(request, message)
                else:
                    messages.error(request, message)
                return redirect('contact_list')
            else:
                # Сохраняем в XML
                if save_contact_to_xml(contact_data):
                    messages.success(request, 'Контакт успешно сохранен в XML файл!')
                    return redirect('contact_list')
                else:
                    messages.error(request, 'Ошибка при сохранении контакта в XML')
    else:
        form = ContactForm()
    
    return render(request, 'contact_form.html', {'form': form})

# Список всех контактов с выбором источника
def contact_list(request):
    source_form = DataSourceForm(request.GET or None)
    source = request.GET.get('source', 'db') #Получаем выбранный источник данных (или 'db' по умолчанию)
    
    if source == 'db':
        contacts = get_all_contacts_from_db()
        from_db = True
    else:
        contacts = get_all_contacts_from_xml()
        from_db = False
    
    context = {
        'contacts': contacts,
        'has_contacts': len(contacts) > 0,
        'source_form': source_form,
        'from_db': from_db,
        'current_source': source
    }
    return render(request, 'contact_list.html', context)

#AJAX поиск контактов в базе данных
def ajax_search(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest': #Если пришёл AJAX-запрос
        query = request.GET.get('q', '').strip() #получаем запрос, при этом убирая пробелы в начале и в конце через .strip()
        
        if query:
            contacts = search_contacts_in_db(query)
            results = []
            for contact in contacts:
                results.append({
                    'id': contact.id,
                    'name': contact.name or '-',
                    'phone': contact.phone or '-',
                    'email': contact.email or '-',
                    'address': contact.address or '-'
                })
            return JsonResponse({'contacts': results, 'query': query})
        else:
            # Если запрос пустой, возвращаем все контакты
            contacts = get_all_contacts_from_db()
            results = []
            for contact in contacts:
                results.append({
                    'id': contact.id,
                    'name': contact.name or '-',
                    'phone': contact.phone or '-',
                    'email': contact.email or '-',
                    'address': contact.address or '-'
                })
            return JsonResponse({'contacts': results})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Редактирование контакта
def edit_contact(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id)
    
    if request.method == 'POST':
        form = ContactEditForm(request.POST, instance=contact)
        if form.is_valid():
            # Проверяем на дубликаты перед сохранением
            name = form.cleaned_data['name']
            phone = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            
            # Ищем дубликаты (исключая текущий контакт)
            duplicate = Contact.objects.filter(
                name=name,
                phone=phone,
                email=email
            ).exclude(id=contact_id).exists()
            
            if duplicate:
                messages.error(request, 'Контакт с такими данными уже существует!')
                return redirect('contact_list')
            else:
                form.save()
                messages.success(request, 'Контакт успешно обновлен!')
                return redirect('contact_list')
    else:
        form = ContactEditForm(instance=contact)
    
    return render(request, 'edit_contact.html', {
        'form': form,
        'contact': contact
    })

# Удаление контакта
def delete_contact(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id)
    
    if request.method == 'POST':
        contact.delete()
        messages.success(request, 'Контакт успешно удален!')
        return redirect('contact_list')
    
    return render(request, 'delete_contact.html', {'contact': contact})

#Загрузка XML файла с контактами
def upload_xml(request):
    if request.method == 'POST':
        form = UploadXMLForm(request.POST, request.FILES)
        if form.is_valid():
            xml_file = request.FILES['xml_file']
            
            # Генерируем безопасное имя файла
            safe_filename = generate_xml_filename()
            upload_dir = ensure_contacts_dir()
            file_path = os.path.join(upload_dir, safe_filename)
            
            # Сохраняем файл
            with open(file_path, 'wb+') as destination:
                for chunk in xml_file.chunks():
                    destination.write(chunk)
            
            # Проверяем валидность XML
            if validate_xml_file(file_path):
                messages.success(request, f'Файл {xml_file.name} успешно загружен и проверен!')
                return redirect('xml_files_list')
            else:
                # Удаляем невалидный файл
                os.remove(file_path)
                messages.error(request, 'Файл не является валидным XML. Файл удален.')
                
    else:
        form = UploadXMLForm()
    
    return render(request, 'upload_xml.html', {'form': form})

#Список всех XML файлов и их содержимого
def xml_files_list(request):
    xml_files = get_all_xml_files()
    
    # Для каждого файла получаем контакты
    files_data = []
    for file_info in xml_files:
        contacts = get_contacts_from_uploaded_xml(file_info['filepath'])
        file_info['contacts'] = contacts
        file_info['contacts_count'] = len(contacts)
        files_data.append(file_info)
    
    context = {
        'files_data': files_data,
        'has_files': len(files_data) > 0
    }
    return render(request, 'xml_files_list.html', context)

#Просмотр содержимого конкретного XML файла
def view_xml_file(request, filename):
    contacts_dir = ensure_contacts_dir()
    file_path = os.path.join(contacts_dir, filename)
    
    if not os.path.exists(file_path):
        messages.error(request, 'Файл не найден')
        return redirect('xml_files_list')
    
    if not validate_xml_file(file_path):
        messages.error(request, 'Файл не является валидным XML')
        return redirect('xml_files_list')
    
    contacts = get_contacts_from_uploaded_xml(file_path)
    
    context = {
        'filename': filename,
        'contacts': contacts,
        'has_contacts': len(contacts) > 0
    }
    return render(request, 'xml_file_detail.html', context)

#Скачивание XML файла
def download_xml_file(request, filename):
    contacts_dir = get_contacts_xml_dir()
    file_path = os.path.join(contacts_dir, filename)
    
    if not os.path.exists(file_path):
        messages.error(request, 'Файл не найден')
        return redirect('xml_files_list')
    
    try:
        # Проверяем, что файл является XML
        if not filename.endswith('.xml'):
            messages.error(request, 'Файл не является XML')
            return redirect('xml_files_list')
        
        # Открываем файл для чтения в бинарном режиме
        response = FileResponse(open(file_path, 'rb'))
        
        # Устанавливаем заголовки для скачивания
        response['Content-Type'] = 'application/xml'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Ошибка при скачивании файла: {str(e)}')

        return redirect('xml_files_list')
