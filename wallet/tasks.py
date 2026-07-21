import time
from celery import shared_task
from decimal import Decimal
from .models import Currency, ExchangeRate

@shared_task
def update_global_exchange_rates_background():
    """
    مهمة ثقيلة تعمل في الخلفية: محاكاة الاتصال بسيرفر خارجي (API) 
    لجلب أسعار الصرف وتحديثها في nabil.sqlite3
    """
    print("⏳ [Celery Background] جاري الاتصال بسيرفر البنك المركزي العالمي لجلب الأسعار...")
    
    # محاكاة تأخير زمني حقيقي (مثلاً تأخير الشبكة والـ API لمدة 5 ثوانٍ)
    time.sleep(5)
    
    try:
        usd = Currency.objects.get(code="USD")
        sar = Currency.objects.get(code="SAR")
        yer = Currency.objects.get(code="YER")
        
        # محاكاة تحديث الأسعار بقيم عشوائية أو جديدة في قاعدة البيانات
        # USD -> YER
        rate_obj, _ = ExchangeRate.objects.update_or_create(
            from_currency=usd,
            to_currency=yer,
            defaults={"rate": Decimal("535.50")} # سعر جديد
        )
        print(f"✅ [Celery Background] تم تحديث صرف USD -> YER بنجاح إلى: {rate_obj.rate}")
        return "تم تحديث أسعار الصرف بنجاح تام!"
        
    except Exception as e:
        return f"❌ خطأ أثناء التحديث الخلفي: {str(e)}"
