from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny  # السماح بالوصول المفتوح بدون توثيق أو أمان للعرض
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Q
from decimal import Decimal
from .models import Wallet, WalletBalance, Transaction, Currency, ExchangeRate

class ProfileView(views.APIView):
    """
    جلب الأرصدة والملف الشخصي للعميل المختار حياً بناءً على اسمه الممرر من الواجهة
    """
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            # قراءة اسم العميل الممرر من الواجهة مباشرة عبر الـ Query Params
            username = request.query_params.get('username', 'nabil')
            user = get_object_or_404(User, username=username)
            wallet, _ = Wallet.objects.get_or_create(user=user)
            balances = WalletBalance.objects.filter(wallet=wallet)
            
            balances_data = []
            for b in balances:
                balances_data.append({
                    "currency_code": b.currency.code,
                    "amount": float(b.amount)
                })
            
            return Response({
                "username": user.username,
                "email": user.email,
                "wallet": {
                    "balances": balances_data
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": f"تعذر جلب ملف العميل: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class TransactionListView(views.APIView):
    """
    جلب سجل العمليات المالية الخاص بالعميل المختار فقط من nabil.sqlite3
    """
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            username = request.query_params.get('username', 'nabil')
            user = get_object_or_404(User, username=username)
            wallet, _ = Wallet.objects.get_or_create(user=user)
            
            # جلب المعاملات التي تخص محفظة هذا العميل (سواء كمرسل أو مستلم في حال التحويل)
            transactions = Transaction.objects.filter(
                Q(wallet=wallet) | Q(counterpart_wallet=wallet)
            ).order_by('-created_at')
            
            tx_data = []
            for tx in transactions:
                tx_data.append({
                    "id": tx.id,
                    "transaction_type": tx.transaction_type,
                    "amount": float(tx.amount),
                    "amount_value": float(tx.amount),
                    "currency_code": tx.from_currency.code if tx.from_currency else "USD",
                    "converted_amount": float(tx.converted_amount) if tx.converted_amount else None,
                    "to_currency_code": tx.to_currency.code if tx.to_currency else "",
                    "created_at": tx.created_at.strftime('%Y-%m-%d %H:%M') if tx.created_at else "-"
                })
                
            return Response(tx_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": f"تعذر جلب العمليات: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class DepositView(views.APIView):
    """
    تنفيذ عملية إيداع مالي حقيقية ومباشرة في قاعدة البيانات للعميل النشط
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        currency_code = request.data.get('currency_code')
        amount = request.data.get('amount')
        
        if not username or not currency_code or not amount:
            return Response({"error": "جميع الحقول (العميل، العملة، المبلغ) مطلوبة!"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = get_object_or_404(User, username=username)
            wallet, _ = Wallet.objects.get_or_create(user=user)
            currency = get_object_or_404(Currency, code=currency_code)
            
            # تعديل وحفظ الرصيد الفعلي في قاعدة البيانات
            balance, _ = WalletBalance.objects.get_or_create(wallet=wallet, currency=currency)
            balance.amount += Decimal(str(amount))
            balance.save()
            
            # تسجيل المعاملة في جدول الحركات التاريخية للشفافية
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='DEPOSIT',
                from_currency=currency,
                amount=Decimal(str(amount))
            )
            
            return Response({"success": "تمت عملية الإيداع المباشر في nabil.sqlite3 بنجاح!"}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": f"فشلت عملية الإيداع: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class TransferView(views.APIView):
    """
    تحويل مالي حقيقي وفوري من محفظة العميل الحالي إلى محفظة عميل نشط آخر
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        receiver_username = request.data.get('receiver_username')
        currency_code = request.data.get('currency_code')
        amount = request.data.get('amount')
        
        if not username or not receiver_username or not currency_code or not amount:
            return Response({"error": "جميع بيانات التحويل مطلوبة!"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            sender = get_object_or_404(User, username=username)
            receiver = get_object_or_404(User, username=receiver_username)
            
            sender_wallet = get_object_or_404(Wallet, user=sender)
            receiver_wallet, _ = Wallet.objects.get_or_create(user=receiver)
            currency = get_object_or_404(Currency, code=currency_code)
            
            # التحقق من توفر رصيد كافٍ لدى المرسل
            sender_balance = WalletBalance.objects.filter(wallet=sender_wallet, currency=currency).first()
            if not sender_balance or sender_balance.amount < Decimal(str(amount)):
                return Response({"error": f"عذراً! رصيدك بالعملة {currency_code} غير كافٍ لإتمام عملية التحويل."}, status=status.HTTP_400_BAD_REQUEST)
                
            # الخصم والإضافة الحية في قاعدة البيانات
            sender_balance.amount -= Decimal(str(amount))
            sender_balance.save()
            
            receiver_balance, _ = WalletBalance.objects.get_or_create(wallet=receiver_wallet, currency=currency)
            receiver_balance.amount += Decimal(str(amount))
            receiver_balance.save()
            
            # تسجيل العملية التاريخية المشتركة
            Transaction.objects.create(
                wallet=sender_wallet,
                counterpart_wallet=receiver_wallet,
                transaction_type='TRANSFER',
                from_currency=currency,
                amount=Decimal(str(amount))
            )
            
            return Response({"success": f"تم تحويل {amount} {currency_code} إلى {receiver_username} بنجاح حقيقي!"}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": f"فشلت عملية التحويل المالي: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class ExchangeView(views.APIView):
    """
    مصارفة وتبديل الأرصدة حياً ومباشراً بداخل نفس المحفظة بالاعتماد على أسعار الصرف الحقيقية
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        from_currency_code = request.data.get('from_currency_code')
        to_currency_code = request.data.get('to_currency_code')
        amount = request.data.get('amount')
        
        if not username or not from_currency_code or not to_currency_code or not amount:
            return Response({"error": "جميع بيانات المصارفة مطلوبة!"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = get_object_or_404(User, username=username)
            wallet = get_object_or_404(Wallet, user=user)
            
            from_currency = get_object_or_404(Currency, code=from_currency_code)
            to_currency = get_object_or_404(Currency, code=to_currency_code)
            
            # التأكد من رصيد العملة المراد صرفها
            source_balance = WalletBalance.objects.filter(wallet=wallet, currency=from_currency).first()
            if not source_balance or source_balance.amount < Decimal(str(amount)):
                return Response({"error": f"رصيدك غير كافٍ بالعملة {from_currency_code} لإتمام المصارفة!"}, status=status.HTTP_400_BAD_REQUEST)
                
            # جلب أسعار الصرف الفعلية والمحسوبة في قاعدة البيانات
            rate_obj = ExchangeRate.objects.filter(from_currency=from_currency, to_currency=to_currency).first()
            if not rate_obj:
                return Response({"error": f"معامل صرف العملات المباشر بين {from_currency_code} و {to_currency_code} غير مهيأ بعد!"}, status=status.HTTP_400_BAD_REQUEST)
                
            converted_amount = Decimal(str(amount)) * rate_obj.rate
            
            # تنفيذ تبديل الأرصدة
            source_balance.amount -= Decimal(str(amount))
            source_balance.save()
            
            target_balance, _ = WalletBalance.objects.get_or_create(wallet=wallet, currency=to_currency)
            target_balance.amount += converted_amount
            target_balance.save()
            
            # تسجيل العملية التاريخية للمصارفة
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='EXCHANGE',
                from_currency=from_currency,
                to_currency=to_currency,
                amount=Decimal(str(amount)),
                converted_amount=converted_amount
            )
            
            return Response({"success": f"تمت المصارفة بنجاح! تم قيد {converted_amount:.2f} {to_currency_code} في حسابك."}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": f"فشلت عملية المصارفة: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)