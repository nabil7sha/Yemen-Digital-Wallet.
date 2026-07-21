from .celery import app as celery_app

# هذا يضمن تحميل التطبيق عند بدء دجانغو
__all__ = ('celery_app',)
