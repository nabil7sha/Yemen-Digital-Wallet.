import os
import sys
import django
from decimal import Decimal

# 1. إعداد بيئة عمل Django للتعرف على موديلات المشروع
# تم تحديثه إلى 'core.settings' ليتطابق مع اسم مجلد الإعدادات الفعلي في مشروعك
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

try:
    django.setup()
    print("✓ تم الاتصال ببيئة عمل Django بنجاح.")
except Exception as e:
    print(f"❌ فشل إعداد بيئة Django: {e}")
    print("ملاحظة: تأكد من تشغيل السكربت من المجلد الرئيسي للمشروع (بجانب ملف manage.py).")
    sys.exit(1)

# استيراد الموديلات بعد تهيئة Django
from django.contrib.auth.models import User
from wallet.models import Currency, Wallet, WalletBalance, Transaction, Profile, ExchangeRate

def populate_db():
    print("\n⏳ جاري بدء عملية تغذية قاعدة البيانات بالبيانات الحية...")

    # 2. إنشاء وتجهيز العملات الأساسية
    print("- جاري إعداد العملات...")
    usd, _ = Currency.objects.get_or_create(code="USD", defaults={"name": "دولار أمريكي", "is_active": True})
    sar, _ = Currency.objects.get_or_create(code="SAR", defaults={"name": "ريال سعودي", "is_active": True})
    yer, _ = Currency.objects.get_or_create(code="YER", defaults={"name": "ريال يمني", "is_active": True})
    eur, _ = Currency.objects.get_or_create(code="EUR", defaults={"name": "يورو", "is_active": True})

    # 3. إعداد أسعار الصرف (Exchange Rates) لعمليات التحويل والمصارفة
    print("- جاري إعداد أسعار الصرف...")
    ExchangeRate.objects.update_or_create(from_currency=usd, to_currency=sar, defaults={"rate": Decimal("3.750000")})
    ExchangeRate.objects.update_or_create(from_currency=sar, to_currency=usd, defaults={"rate": Decimal("0.266667")})
    ExchangeRate.objects.update_or_create(from_currency=usd, to_currency=yer, defaults={"rate": Decimal("530.000000")})
    ExchangeRate.objects.update_or_create(from_currency=yer, to_currency=usd, defaults={"rate": Decimal("0.001886")})

    # دالة مساعدة لإنشاء مستخدمين ومحافظهم
    def create_user_with_wallet(username, email, password, phone, balances):
        user, created = User.objects.get_or_create(username=username, defaults={"email": email})
        if created:
            user.set_password(password)
            user.save()
            print(f"  + تم إنشاء حساب جديد للمستخدم: {username}")
        else:
            print(f"  ~ مستخدم موجود مسبقاً: {username}")

        # إنشاء الملف الشخصي
        Profile.objects.get_or_create(user=user, defaults={"phone_number": phone})
        
        # إنشاء المحفظة
        wallet, _ = Wallet.objects.get_or_create(user=user)
        
        # توزيع الأرصدة المدخلة
        for currency, amount in balances.items():
            WalletBalance.objects.update_or_create(
                wallet=wallet, 
                currency=currency, 
                defaults={"amount": Decimal(str(amount))}
            )
        return user, wallet

    # 4. إنشاء مستخدمين تجريبيين ذوي أرصدة حقيقية في البنك الرقمي
    print("- جاري إنشاء المحافظ وتوزيع الأرصدة...")
    
    # المستخدم الأول: أحمد
    user_ahmed, wallet_ahmed = create_user_with_wallet(
        username="ahmed",
        email="ahmed@example.com",
        password="password123",
        phone="+966500000000",
        balances={usd: 15500.00, sar: 42000.00, eur: 5000.00}
    )

    # المستخدم الثاني: محمد
    user_mohammed, wallet_mohammed = create_user_with_wallet(
        username="nabil",
        email="mohammed@example.com",
        password="password123",
        phone="+967770000000",
        balances={usd: 8400.00, yer: 950000.00}
    )

    # المستخدم الثالث: ياسمين
    user_yasmin, wallet_yasmin = create_user_with_wallet(
        username="yasmin",
        email="yasmin@example.com",
        password="password123",
        phone="+966512345678",
        balances={usd: 2450.00, sar: 15000.00, eur: 3200.00}
    )

    # 5. تسجيل بعض العمليات المالية الحية في سجل المعاملات (Transactions)
    print("- جاري تسجيل العمليات المالية التاريخية...")
    
    # تفريغ العمليات القديمة لتجنب تكرار البيانات أثناء العرض التقديمي (اختياري)
    Transaction.objects.all().delete()

    # العملية 1: إيداع مباشر لأحمد بقيمة 5000 دولار
    Transaction.objects.create(
        wallet=wallet_ahmed,
        transaction_type='DEPOSIT',
        from_currency=usd,
        amount=Decimal("5000.00"),
        converted_amount=None
    )

    # العملية 2: تحويل مالي بقيمة 150 دولار من أحمد إلى محمد
    Transaction.objects.create(
        wallet=wallet_ahmed,
        counterpart_wallet=wallet_mohammed,
        transaction_type='TRANSFER',
        from_currency=usd,
        amount=Decimal("150.00"),
        converted_amount=None
    )

    # العملية 3: مصارفة عملات داخل محفظة محمد (تحويل 1000 دولار إلى 530,000 ريال يمني)
    Transaction.objects.create(
        wallet=wallet_mohammed,
        transaction_type='EXCHANGE',
        from_currency=usd,
        to_currency=yer,
        amount=Decimal("1000.00"),
        converted_amount=Decimal("530000.00")
    )

    # العملية 4: إيداع مباشر لياسمين بقيمة 12,000 ريال سعودي
    Transaction.objects.create(
        wallet=wallet_yasmin,
        transaction_type='DEPOSIT',
        from_currency=sar,
        amount=Decimal("12000.00"),
        converted_amount=None
    )

    # العملية 5: تحويل مالي بقيمة 350 يورو من ياسمين إلى أحمد
    Transaction.objects.create(
        wallet=wallet_yasmin,
        counterpart_wallet=wallet_ahmed,
        transaction_type='TRANSFER',
        from_currency=eur,
        amount=Decimal("350.00"),
        converted_amount=None
    )

    print("\n🚀 تمت عملية تغذية قاعدة البيانات بنجاح تام!")
    print(f"   - عدد العملات الكلي: {Currency.objects.count()}")
    print(f"   - عدد المستخدمين: {User.objects.count()}")
    print(f"   - إجمالي الأرصدة والمحافظ: {WalletBalance.objects.count()}")
    print(f"   - إجمالي العمليات المسجلة: {Transaction.objects.count()}")

if __name__ == "__main__":
    populate_db()