from django import forms
import re
from .models import Contact

#Форма для добавления контакта
class ContactForm(forms.Form):
    SAVE_CHOICES = [
        ('db', 'Сохранить в базу данных'),
        ('xml', 'Сохранить в XML файл'),
    ]
    
    name = forms.CharField(
        label='ФИО',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label='Телефон',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        label='Адрес',
        max_length=200,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    save_to = forms.ChoiceField(
        label='Куда сохранить',
        choices=SAVE_CHOICES,
        initial='db',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    # Валидация данных
    def clean_name(self):
        name = self.cleaned_data['name']
        if not re.match(r'^[а-яА-Яa-zA-Z\s\-\.]+$', name):
            raise forms.ValidationError('ФИО может содержать только буквы, пробелы, дефисы и точки')
        return name

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if not re.match(r'^[\d\s\-\(\)\+]+$', phone):
            raise forms.ValidationError('Некорректный формат телефона')
        return phone

#Форма для редактирования контакта
class ContactEditForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

#Форма для отображения данных
class DataSourceForm(forms.Form):
    SOURCE_CHOICES = [
        ('db', 'База данных'),
        ('xml', 'XML файлы'),
    ]
    
    source = forms.ChoiceField(
        label='Источник данных',
        choices=SOURCE_CHOICES,
        initial='db',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'source-selector'})
    )

#Форма для загрузки xml
class UploadXMLForm(forms.Form):
    xml_file = forms.FileField(
        label='XML файл',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xml'})
    )