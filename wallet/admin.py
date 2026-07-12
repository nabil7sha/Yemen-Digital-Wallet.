from django.contrib import admin


from .models import Currency, Wallet, WalletBalance, Transaction, Profile, ExchangeRate

# 1. تنسيق جدول العملات
@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')  # الأعمدة التي تظهر في الجدول
    list_filter = ('is_active',)                  # أداة فلترة سريعة على اليسار
    search_fields = ('code', 'name')              # صندوق البحث

# 2. تنسيق جدول أسعار الصرف
@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('from_currency', 'to_currency', 'rate')
    list_editable = ('rate',)                     # تعديل السعر فوراً من الجدول بدون فتح صفحة جديدة
    search_fields = ('from_currency__code', 'to_currency__code')

# 3. تنسيق جدول المحافظ
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
    search_fields = ('user__username', 'user__email')

# 4. تنسيق جدول أرصدة المحافظ
@admin.register(WalletBalance)
class WalletBalanceAdmin(admin.ModelAdmin):
    list_display = ('wallet_owner', 'currency', 'amount')
    list_filter = ('currency',)
    search_fields = ('wallet__user__username', 'currency__code')

    # دالة مساعدة لإظهار اسم صاحب المحفظة بوضوح في لوحة التحكم
    def wallet_owner(self, obj):
        return obj.wallet.user.username
    wallet_owner.short_description = 'صاحب المحفظة'

# 5. تنسيق سجل العمليات المالية
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender_username', 'receiver_username', 'transaction_type', 'amount', 'from_currency', 'created_at')
    list_filter = ('transaction_type', 'from_currency', 'created_at')
    search_fields = ('wallet__user__username', 'counterpart_wallet__user__username')
    readonly_fields = ('created_at',)  # جعل التاريخ للقراءة فقط لمنع التلاعب

    def sender_username(self, obj):
        return obj.wallet.user.username if obj.wallet else "نظام عام"
    sender_username.short_description = 'المرسل'

    def receiver_username(self, obj):
        return obj.counterpart_wallet.user.username if obj.counterpart_wallet else "-"
    receiver_username.short_description = 'المستلم'

# 6. تنسيق الملفات الشخصية للعملاء
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number')
    search_fields = ('user__username', 'phone_number')
