from celery import shared_task
import requests
from decimal import Decimal
from .models import Currency, ExchangeRate

# خريطة لأسماء العملات الشائعة باللغة العربية
CURRENCY_NAMES = {
    "USD": "دولار أمريكي",
    "EUR": "يورو",
    "SAR": "ريال سعودي",
    "YER": "ريال يمني",
    "GBP": "جنيه إسترليني",
    "JPY": "ين ياباني",
    "CAD": "دولار كندي",
    "AED": "درهم إماراتي",
}

@shared_task
def update_global_exchange_rates_background(auto_create_missing=False):
    """
    تحديث أسعار الصرف الحية من Frankfurter API وتوفير التحديث العكسي
    :param auto_create_missing: إذا كانت True، سيقوم النظام بإنشاء العملات الجديدة تلقائياً
    """
    print("⏳ [Celery Task] جاري الاتصال بسيرفر أسعار الصرف Frankfurter API...")
    
    try:
        # 1. جلب أو إنشاء عملة الأساس USD
        usd, _ = Currency.objects.get_or_create(
            code="USD", 
            defaults={"name": CURRENCY_NAMES.get("USD", "دولار أمريكي"), "is_active": True}
        )

        # 2. الاتصال بـ API أسعار الصرف العالمية
        response = requests.get(
            "https://api.frankfurter.app/latest?from=USD",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        rates_data = data.get("rates", {})
        updated_count = 0

        # 3. تحديث العملات المدعومة دولياً
        for currency_code, rate in rates_data.items():
            rate_decimal = Decimal(str(rate))

            if auto_create_missing:
                # إنشاء العملة إذا لم تكن موجودة
                to_currency, _ = Currency.objects.get_or_create(
                    code=currency_code,
                    defaults={
                        "name": CURRENCY_NAMES.get(currency_code, f"عملة {currency_code}"),
                        "is_active": True
                    }
                )
            else:
                # تحديث العملات المضافة مسبقاً فقط
                try:
                    to_currency = Currency.objects.get(code=currency_code)
                except Currency.DoesNotExist:
                    continue

            # تحديث USD -> Currency
            ExchangeRate.objects.update_or_create(
                from_currency=usd,
                to_currency=to_currency,
                defaults={"rate": rate_decimal}
            )

            # تحديث السعر العكسي تلقائياً Currency -> USD
            if rate_decimal > 0:
                ExchangeRate.objects.update_or_create(
                    from_currency=to_currency,
                    to_currency=usd,
                    defaults={"rate": Decimal("1") / rate_decimal}
                )

            print(f"✅ تم تحديث صرف USD ⇆ {currency_code} = {rate_decimal}")
            updated_count += 1

        # 4. معالجة العملات المحلية غير المدرجة في النشرة الدولية (مثل YER)
        try:
            yer_currency = Currency.objects.get(code="YER")
            yer_rate = Decimal("530.00")
            ExchangeRate.objects.update_or_create(
                from_currency=usd,
                to_currency=yer_currency,
                defaults={"rate": yer_rate}
            )
            ExchangeRate.objects.update_or_create(
                from_currency=yer_currency,
                to_currency=usd,
                defaults={"rate": Decimal("1") / yer_rate}
            )
            print("✅ تم تثبيت/تحديث أسعار صرف الريال اليمني YER بنجاح")
            updated_count += 1
        except Currency.DoesNotExist:
            pass

        result_msg = f"🎉 تم تحديث {updated_count} سعر صرف في nabil.sqlite3 بنجاح!"
        print(result_msg)
        return result_msg

    except requests.RequestException as e:
        error_msg = f"❌ خطأ في الاتصال بالـ API الخارجي: {str(e)}"
        print(error_msg)
        return error_msg

    except Exception as e:
        error_msg = f"❌ حدث عطل غير متوقع أثناء التحديث: {str(e)}"
        print(error_msg)
        return error_msg