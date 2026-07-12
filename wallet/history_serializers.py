from rest_framework import serializers
from .models import Transaction, Notification, Currency

class TransactionDetailSerializer(serializers.ModelSerializer):    # جلب رموز العملات كنصوص بدلاً من أرقام المعرفات ID
    from_currency = serializers.CharField(source='from_currency.code')
    to_currency = serializers.CharField(source='to_currency.code', allow_null=True)
    
    # جلب اسم المستخدم لصاحب المحفظة والطرف الآخر إن وجد
    wallet_user = serializers.CharField(source='wallet.user.username')
    counterpart_user = serializers.CharField(source='counterpart_wallet.user.username', allow_null=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 
            'wallet_user',
            'counterpart_user',
            'transaction_type', 
            'from_currency', 
            'to_currency', 
            'amount', 
            'converted_amount', 
            'created_at'
        ]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'is_read', 'created_at']