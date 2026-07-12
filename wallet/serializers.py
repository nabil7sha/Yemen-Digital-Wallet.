from rest_framework import serializers
from decimal import Decimal
from .models import Currency, Transaction, WalletBalance

class DepositSerializer(serializers.Serializer):
    currency_code = serializers.CharField(max_length=3)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0.01'))

    def validate_currency_code(self, value):
        code = value.upper()
        if not Currency.objects.filter(code=code, is_active=True).exists():
            raise serializers.ValidationError("هذه العملة غير مدعومة أو غير نشطة حالياً.")
        return code


class TransferSerializer(serializers.Serializer):
    receiver_username = serializers.CharField()
    currency_code = serializers.CharField(max_length=3)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0.01'))

    def validate_currency_code(self, value):
        return value.upper()


class ExchangeSerializer(serializers.Serializer):
    from_currency_code = serializers.CharField(max_length=3)
    to_currency_code = serializers.CharField(max_length=3)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0.01'))

    def validate(self, data):
        from_code = data['from_currency_code'].upper()
        to_code = data['to_currency_code'].upper()
        
        if from_code == to_code:
            raise serializers.ValidationError("لا يمكن تحويل العملة إلى نفس العملة.")
        
        data['from_currency_code'] = from_code
        data['to_currency_code'] = to_code
        return data


class TransactionResponseSerializer(serializers.ModelSerializer):
    from_currency = serializers.CharField(source='from_currency.code')
    to_currency = serializers.CharField(source='to_currency.code', allow_null=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'transaction_type', 'amount', 'from_currency', 'to_currency', 'converted_amount', 'created_at']