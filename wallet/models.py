from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True) # مثال: USD, EUR, SAR
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class ExchangeRate(models.Model):
    from_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='rates_from')
    to_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='rates_to')
    rate = models.DecimalField(max_digits=12, decimal_places=6) # دقة عالية لأسعار الصرف
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('from_currency', 'to_currency')

    def __str__(self):
        return f"1 {self.from_currency} = {self.rate} {self.to_currency}"


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wallet - {self.user.username}"


class WalletBalance(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='balances')
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        unique_together = ('wallet', 'currency')

    def __str__(self):
        return f"{self.wallet.user.username} | {self.amount} {self.currency.code}"


class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('DEPOSIT', 'Deposit'),
        ('TRANSFER', 'Transfer'),
        ('EXCHANGE', 'Currency Exchange'),
    )

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    # في حال التحويل، نحدد المحفظة المستلمة كـ Foreign Key اختياري
    counterpart_wallet = models.ForeignKey(Wallet, on_delete=models.SET_NULL, null=True, blank=True, related_name='counterpart_transactions')
    
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    
    # تفاصيل العملة والمبالغ
    from_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='tx_from_currency')
    to_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True, related_name='tx_to_currency')
    
    amount = models.DecimalField(max_digits=15, decimal_places=2) # المبلغ الأساسي بالعملة الأصلية
    converted_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True) # يُستخدم في التحويل والصرف
    
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # منع التحويل لنفس المحفظة برممجياً على مستوى الموديل كحماية إضافية
        if self.transaction_type == 'TRANSFER' and self.wallet == self.counterpart_wallet:
            raise ValidationError("Cannot transfer money to the same wallet.")

    def __str__(self):
        return f"{self.transaction_type} | {self.amount} {self.from_currency.code} | {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} - Read: {self.is_read}"