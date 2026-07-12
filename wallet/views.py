from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import Wallet, WalletBalance, Transaction, Currency, ExchangeRate

# =======================================================
# 1️⃣ دالة رندرة الـ HTML مع الـ Context لصفحة العميل (User)
# =======================================================
def user_dashboard_template_view(request):
    """
    تسحب هذه الدالة بيانات العميل وتمررها عبر الـ Context لـ dashboard.html
    """
    username = request.GET.get('username', 'nabil')
    user = get_object_or_404(User, username=username)
    
    wallet, _ = Wallet.objects.get_or_create(user=user)
    balances = WalletBalance.objects.filter(wallet=wallet)
    
    balances_map = {b.currency.code: b.amount for b in balances}
    
    # جلب الحركات المالية الخاصة بهذا العميل
    transactions = Transaction.objects.filter(
        Q(wallet=wallet) | Q(counterpart_wallet=wallet)
    ).order_by('-created_at')
    
    all_users = User.objects.all()

    context = {
        'active_user': user,
        'usd_balance': balances_map.get('USD', Decimal('0.00')),
        'sar_balance': balances_map.get('SAR', Decimal('0.00')),
        'yer_balance': balances_map.get('YER', Decimal('0.00')),
        'eur_balance': balances_map.get('EUR', Decimal('0.00')),
        'transactions': transactions,
        'all_users': all_users,
    }

    return render(request, 'wallet/dashboard.html', context)


# =======================================================
# 2️⃣ دالة رندرة الـ HTML مع الـ Context لصفحة المسؤول (Admin)
# =======================================================
def admin_dashboard_template_view(request):
    """
    تسحب هذه الدالة إحصائيات النظام بالكامل والسيولة وتمررها لـ admin_dashboard.html
    """
    # إحصائيات عامة من قاعدة البيانات
    total_users = User.objects.count()
    total_wallets = Wallet.objects.count()
    total_transactions = Transaction.objects.count()

    # حساب السيولة المتوفرة مقسمة بالعملات
    balances_by_currency = WalletBalance.objects.values('currency__code').annotate(
        total_balance=Sum('amount')
    )
    balances_summary = []
    for item in balances_by_currency:
        balances_summary.append({
            "currency": item['currency__code'],
            "total_amount": float(item['total_balance'] or 0)
        })

    # جلب جميع الحركات والعمليات المالية التاريخية لجميع المحافظ
    transactions = Transaction.objects.all().order_by('-created_at')

    # جلب جميع أسعار الصرف الحية
    exchange_rates = ExchangeRate.objects.all().order_by('from_currency__code')

    # بناء الـ Context الشامل للإدارة
    context = {
        "total_users": total_users,
        "total_wallets": total_wallets,
        "total_transactions": total_transactions,
        "balances_summary": balances_summary,
        "transactions": transactions,
        "exchange_rates": exchange_rates,
    }

    return render(request, 'wallet/admin_dashboard.html', context)


# =======================================================
# 3️⃣ واجهات الـ APIs المفتوحة للعمليات المالية الفورية (POST / GET)
# =======================================================
class ProfileView(views.APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        username = request.GET.get('username', 'nabil')
        user = get_object_or_404(User, username=username)
        wallet, _ = Wallet.objects.get_or_create(user=user)
        balances = WalletBalance.objects.filter(wallet=wallet)
        
        balances_data = [{
            "currency_code": b.currency.code,
            "amount": float(b.amount)
        } for b in balances]
        
        return Response({
            "username": user.username,
            "email": user.email,
            "wallet": {
                "id": wallet.id,
                "balances": balances_data
            }
        }, status=status.HTTP_200_OK)

class TransactionListView(views.APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        username = request.GET.get('username', 'nabil')
        user = get_object_or_404(User, username=username)
        wallet, _ = Wallet.objects.get_or_create(user=user)
        transactions = Transaction.objects.filter(
            Q(wallet=wallet) | Q(counterpart_wallet=wallet)
        ).order_by('-created_at')
        
        tx_data = [{
            "transaction_type": tx.transaction_type,
            "amount": float(tx.amount),
            "currency_code": tx.from_currency.code,
            "converted_amount": float(tx.converted_amount) if tx.converted_amount else None,
            "to_currency_code": tx.to_currency.code if tx.to_currency else "",
            "created_at": tx.created_at.strftime('%Y-%m-%d %H:%M')
        } for tx in transactions]
        
        return Response(tx_data, status=status.HTTP_200_OK)

class DepositView(views.APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        currency_code = request.data.get('currency_code')
        amount = request.data.get('amount')
        
        try:
            user = get_object_or_404(User, username=username)
            wallet, _ = Wallet.objects.get_or_create(user=user)
            currency = get_object_or_404(Currency, code=currency_code)
            
            balance, _ = WalletBalance.objects.get_or_create(wallet=wallet, currency=currency)
            balance.amount += Decimal(str(amount))
            balance.save()
            
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='DEPOSIT',
                from_currency=currency,
                amount=Decimal(str(amount))
            )
            return Response({"success": "تمت عملية الإيداع بنجاح!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class TransferView(views.APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        receiver_username = request.data.get('receiver_username')
        currency_code = request.data.get('currency_code')
        amount = request.data.get('amount')
        
        try:
            sender = get_object_or_404(User, username=username)
            receiver = get_object_or_404(User, username=receiver_username)
            sender_wallet = get_object_or_404(Wallet, user=sender)
            receiver_wallet, _ = Wallet.objects.get_or_create(user=receiver)
            currency = get_object_or_404(Currency, code=currency_code)
            
            sender_balance = WalletBalance.objects.filter(wallet=sender_wallet, currency=currency).first()
            if not sender_balance or sender_balance.amount < Decimal(str(amount)):
                return Response({"error": "عذراً! رصيدك غير كافٍ لإتمام عملية التحويل."}, status=status.HTTP_400_BAD_REQUEST)
                
            sender_balance.amount -= Decimal(str(amount))
            sender_balance.save()
            
            receiver_balance, _ = WalletBalance.objects.get_or_create(wallet=receiver_wallet, currency=currency)
            receiver_balance.amount += Decimal(str(amount))
            receiver_balance.save()
            
            Transaction.objects.create(
                wallet=sender_wallet,
                counterpart_wallet=receiver_wallet,
                transaction_type='TRANSFER',
                from_currency=currency,
                amount=Decimal(str(amount))
            )
            return Response({"success": "تم التحويل بنجاح!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ExchangeView(views.APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        from_currency_code = request.data.get('from_currency_code')
        to_currency_code = request.data.get('to_currency_code')
        amount = request.data.get('amount')
        
        try:
            user = get_object_or_404(User, username=username)
            wallet = get_object_or_404(Wallet, user=user)
            from_currency = get_object_or_404(Currency, code=from_currency_code)
            to_currency = get_object_or_404(Currency, code=to_currency_code)
            
            source_balance = WalletBalance.objects.filter(wallet=wallet, currency=from_currency).first()
            if not source_balance or source_balance.amount < Decimal(str(amount)):
                return Response({"error": "رصيدك غير كافٍ لإتمام المصارفة!"}, status=status.HTTP_400_BAD_REQUEST)
                
            rate_obj = ExchangeRate.objects.filter(from_currency=from_currency, to_currency=to_currency).first()
            if not rate_obj:
                return Response({"error": "سعر صرف هذه العملات غير مهيأ بعد!"}, status=status.HTTP_400_BAD_REQUEST)
                
            converted_amount = Decimal(str(amount)) * rate_obj.rate
            
            source_balance.amount -= Decimal(str(amount))
            source_balance.save()
            
            target_balance, _ = WalletBalance.objects.get_or_create(wallet=wallet, currency=to_currency)
            target_balance.amount += converted_amount
            target_balance.save()
            
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='EXCHANGE',
                from_currency=from_currency,
                to_currency=to_currency,
                amount=Decimal(str(amount)),
                converted_amount=converted_amount
            )
            return Response({"success": "تمت المصارفة بنجاح!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)