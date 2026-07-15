from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test  # 🔐 استيراد حارس المسؤولين والجلسات
from django.db.models import Q, Sum
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from .models import Wallet, WalletBalance, Transaction, Currency, ExchangeRate

def custom_login_view(request):
    """رندرة ومعالجة صفحة تسجيل الدخول الفاخرة للعملاء"""
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard_luminous')
        return redirect('user_dashboard_luminous')
        
    error_message = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)  # تسجيل الدخول في نظام Django للجلسات
            return redirect('user_dashboard_luminous')
        else:
            error_message = "اسم المستخدم أو كلمة المرور غير صحيحة!"
            
    return render(request, 'wallet/login.html', {'error_message': error_message})


def custom_logout_view(request):
    """تسجيل خروج العميل وتصفية الجلسة بالكامل"""
    logout(request)
    return redirect('user_login_luminous')


def admin_login_view(request):
    """رندرة ومعالجة صفحة تسجيل دخول الأدمن والمشرفين (Superuser)"""
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard_luminous')
        
    error_message = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)  # تسجيل دخول المسؤول في الجلسة
            return redirect('admin_dashboard_luminous')
        else:
            error_message = "عذراً! لا تملك الصلاحيات الإشرافية المطلوبة أو البيانات خاطئة."
            
    return render(request, 'wallet/admin_login.html', {'error_message': error_message})


def admin_logout_view(request):
    """تسجيل خروج الأدمن وتوجيهه لشاشة الدخول المخصصة للمسؤولين"""
    logout(request)
    return redirect('admin_login_luminous')


@login_required(login_url='user_login_luminous')  # 🔐 حماية المسار وتوجيهه لصفحة الدخول المناسبة
def user_dashboard_template_view(request):
    """رندرة لوحة التحكم للعملاء مع الـ Context الآمن"""
    user = request.user  # الحصول على المستخدم الفعلي المسجل دخوله بأمان
    
    wallet, _ = Wallet.objects.get_or_create(user=user)
    balances = WalletBalance.objects.filter(wallet=wallet)
    balances_map = {b.currency.code: b.amount for b in balances}
    
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


@user_passes_test(lambda u: u.is_superuser, login_url='admin_login_luminous')  # 🔐 قصر التصفح فقط على الأدمن المالي
def admin_dashboard_template_view(request):
    """رندرة لوحة تحكم المسؤول (الأدمن) بعد التأكد من رتبته الإشرافية"""
    total_users = User.objects.count()
    total_wallets = Wallet.objects.count()
    total_transactions = Transaction.objects.count()

    balances_by_currency = WalletBalance.objects.values('currency__code').annotate(
        total_balance=Sum('amount')
    )
    balances_summary = []
    for item in balances_by_currency:
        balances_summary.append({
            "currency": item['currency__code'],
            "total_amount": float(item['total_balance'] or 0)
        })

    transactions = Transaction.objects.all().order_by('-created_at')
    exchange_rates = ExchangeRate.objects.all().order_by('from_currency__code')

    context = {
        "total_users": total_users,
        "total_wallets": total_wallets,
        "total_transactions": total_transactions,
        "balances_summary": balances_summary,
        "transactions": transactions,
        "exchange_rates": exchange_rates,
    }
    return render(request, 'wallet/admin_dashboard.html', context)


class DualLoginView(views.APIView):
    """
    واجهة تسجيل دخول مزدوجة:
    1. تقوم بإنشاء جلسة Django (Session Cookie) لخدمة رندرة قوالب الـ HTML.
    2. تقوم بتوليد JWT Token (Access & Refresh) لخدمة وتأمين طلبات الـ APIs المالية والرقابية.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)  # تسجيل الدخول في نظام Django للجلسات
            
            # توليد رموز JWT المشفرة للمستخدم
            refresh = RefreshToken.for_user(user)
            return Response({
                "success": "تم تسجيل الدخول وتوليد الرموز بنجاح!",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "username": user.username,
                "email": user.email,
                "is_superuser": user.is_superuser  # إبلاغ الواجهة الأمامية بالرتبة الإشرافية
            }, status=status.HTTP_200_OK)
            
        return Response({"error": "اسم المستخدم أو كلمة المرور غير صحيحة!"}, status=status.HTTP_401_UNAUTHORIZED)


class DepositView(views.APIView):
    """إيداع مالي آمن - يتطلب توقيع JWT Token صالح"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        currency_code = request.data.get('currency_code')
        amount = request.data.get('amount')
        
        try:
            user = request.user 
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
            return Response({"success": "تمت عملية الإيداع بنجاح آمن!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TransferView(views.APIView):
    """تحويل مالي آمن لعميل آخر - يتطلب توقيع JWT Token صالح"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        receiver_username = request.data.get('receiver_username')
        currency_code = request.data.get('currency_code')
        amount = request.data.get('amount')
        
        try:
            sender = request.user  # صاحب التوكن الموثق
            receiver = get_object_or_404(User, username=receiver_username)
            
            if sender == receiver:
                return Response({"error": "لا يمكنك التحويل لنفسك!"}, status=status.HTTP_400_BAD_REQUEST)
                
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
            return Response({"success": f"تم تحويل {amount} {currency_code} بنجاح!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ExchangeView(views.APIView):
    """مصارفة وتبديل عملات حية - تتطلب توقيع JWT Token صالح"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from_currency_code = request.data.get('from_currency_code')
        to_currency_code = request.data.get('to_currency_code')
        amount = request.data.get('amount')
        
        try:
            user = request.user
            wallet = get_object_or_404(Wallet, user=user)
            from_currency = get_object_or_404(Currency, code=from_currency_code)
            to_currency = get_object_or_404(Currency, code=to_currency_code)
            
            source_balance = WalletBalance.objects.filter(wallet=wallet, currency=from_currency).first()
            if not source_balance or source_balance.amount < Decimal(str(amount)):
                return Response({"error": "رصيدك غير كافٍ لإتمام عملية المصارفة!"}, status=status.HTTP_400_BAD_REQUEST)
                
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
            return Response({"success": "تمت عملية المصارفة وحفظها بنجاح!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)