import os
import uuid
from django.db import models
import xml.etree.ElementTree as ET
from django.conf import settings
from xml.etree.ElementTree import ParseError
from .models import Contact


#           Работа с БД         #


#Сохраняет контакт в базу данных с проверкой на дубликаты
def save_contact_to_db(contact_data):
    try:
        # Проверяем на дубликат
        duplicate = Contact.objects.filter(
            name=contact_data['name'],
            phone=contact_data['phone'],
            email=contact_data['email']
        ).exists()
        
        if duplicate:
            return False, "Контакт уже существует в базе данных"
        
        # Создаем новый контакт
        contact = Contact.objects.create(
            name=contact_data['name'],
            phone=contact_data['phone'],
            email=contact_data['email'],
            address=contact_data.get('address', '')
        )
        return True, "Контакт успешно сохранен в базу данных"
    
    except Exception as e:
        return False, f"Ошибка при сохранении в БД: {str(e)}"

#Поиск контактов в базе данных
def search_contacts_in_db(query):
    if not query:
        return Contact.objects.all()
    
    return Contact.objects.filter(
        models.Q(name__icontains=query) |
        models.Q(phone__icontains=query) |
        models.Q(email__icontains=query) |
        models.Q(address__icontains=query)
    ).order_by('-created_at')

#Получает все контакты из базы данных
def get_all_contacts_from_db():
    return Contact.objects.all().order_by('-created_at')


#           Работа с XML            #


#Возвращает путь к директории для XML файлов контактов
def get_contacts_xml_dir():
    return os.path.join(settings.MEDIA_ROOT, 'contacts_xml')

#Создает директорию для XML файлов контактов
def ensure_contacts_dir():
    contacts_dir = get_contacts_xml_dir()
    if not os.path.exists(contacts_dir):
        os.makedirs(contacts_dir)
    return contacts_dir

#Генерирует уникальное имя для XML файла
def generate_xml_filename():
    return f"contacts_{uuid.uuid4().hex[:8]}.xml"

#Сохраняет контакт в XML файл
def save_contact_to_xml(contact_data):
    contacts_dir = ensure_contacts_dir()
    file_path = os.path.join(contacts_dir, 'contacts.xml')  # ← Используем contacts.xml как основной файл
    
    try:
        if os.path.exists(file_path):
            # Если файл существует, добавляем новый контакт
            tree = ET.parse(file_path)
            root = tree.getroot()
        else:
            # Создаем новый файл
            root = ET.Element('Contacts')
            tree = ET.ElementTree(root)
        
        # Создаем элемент контакта
        contact = ET.Element('Contact')
        
        ET.SubElement(contact, 'Name').text = contact_data['name']
        ET.SubElement(contact, 'Phone').text = contact_data['phone']
        ET.SubElement(contact, 'Email').text = contact_data['email']
        if contact_data.get('address'):
            ET.SubElement(contact, 'Address').text = contact_data['address']
        
        root.append(contact)
        
        # Сохраняем файл
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        return True
        
    except Exception as e:
        print(f"Error saving to XML: {e}")
        return False

#Получает все контакты из основного XML файла
def get_all_contacts_from_xml():
    contacts_dir = get_contacts_xml_dir()
    file_path = os.path.join(contacts_dir, 'contacts.xml')
    contacts = []
    
    if not os.path.exists(file_path):
        return contacts
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        for contact_elem in root.findall('Contact'):
            contact = {
                'name': contact_elem.find('Name').text if contact_elem.find('Name') is not None else '',
                'phone': contact_elem.find('Phone').text if contact_elem.find('Phone') is not None else '',
                'email': contact_elem.find('Email').text if contact_elem.find('Email') is not None else '',
                'address': contact_elem.find('Address').text if contact_elem.find('Address') is not None else '',
            }
            contacts.append(contact)
            
    except (ParseError, ET.ParseError) as e:
        print(f"Error parsing XML: {e}")
    
    return contacts

#Проверяет валидность XML файла
def validate_xml_file(file_path):
    try:
        ET.parse(file_path)
        return True
    except (ParseError, ET.ParseError):
        return False

#Извлекает контакты из загруженного XML файла
def get_contacts_from_uploaded_xml(file_path):
    contacts = []
    
    if not validate_xml_file(file_path):
        return contacts
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        for contact_elem in root.findall('.//Contact'):
            contact = {}
            
            name_elem = contact_elem.find('Name')
            phone_elem = contact_elem.find('Phone')
            email_elem = contact_elem.find('Email')
            address_elem = contact_elem.find('Address')
            
            if name_elem is not None:
                contact['name'] = name_elem.text
            if phone_elem is not None:
                contact['phone'] = phone_elem.text
            if email_elem is not None:
                contact['email'] = email_elem.text
            if address_elem is not None:
                contact['address'] = address_elem.text
            
            if contact:  # Добавляем только если есть хотя бы одно поле
                contacts.append(contact)
                
    except Exception as e:
        print(f"Error reading uploaded XML: {e}")
    
    return contacts

#Возвращает список всех XML файлов в директории
def get_all_xml_files():
    contacts_dir = ensure_contacts_dir()
    xml_files = []
    
    for filename in os.listdir(contacts_dir):
        if filename.endswith('.xml'):
            file_path = os.path.join(contacts_dir, filename)
            file_info = {
                'filename': filename,
                'filepath': file_path,
                'size': os.path.getsize(file_path),
                'is_valid': validate_xml_file(file_path)
            }
            xml_files.append(file_info)
    
    return xml_files