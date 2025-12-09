from django.db import models

class Contact(models.Model):
    name = models.CharField(max_length=100, verbose_name='ФИО')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(verbose_name='Email')
    address = models.TextField(blank=True, null=True, verbose_name='Адрес')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta: #метаданные таблицы
        db_table = 'contacts'
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'
        unique_together = ['name', 'phone', 'email']  # Для проверки дубликатов
    
    def __str__(self):
        return self.name