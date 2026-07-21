import os
from celery import Celery

# 1. تعيين ملف الإعدادات الافتراضي لدجانغو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# 2. إنشاء كائن التطبيق الخاص بـ Celery
app = Celery('core')

# 3. قراءة الإعدادات من settings.py باستخدام بادئة خاصة (CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# 4. البحث التلقائي عن المهام (Tasks) بداخل جميع التطبيقات المسجلة (مثل ملف wallet/tasks.py)
app.autodiscover_tasks()
