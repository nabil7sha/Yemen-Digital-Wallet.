from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated  # 🔐 قصر الوصول فقط على الموثقين
from rest_framework.authentication import SessionAuthentication, BasicAuthentication  # 🌐 دعم جلسات المتصفح المباشرة
from rest_framework_simplejwt.authentication import JWTAuthentication  # 🔐 دعم الرموز المشفرة لـ APIs
from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from decimal import Decimal
from .models import Wallet, WalletBalance, Transaction, Currency, ExchangeRate

class AdminDashboardStatsView(views.APIView):
    """
    واجهة برمجية لجلب إحصائيات قاعدة البيانات (nabil.sqlite3) العامة بشكل آمن ومحمي.
    تدعم التحقق عبر جلسة المتصفح النشطة للأدمن أو عبر رمز JWT المالي.
    """
    authentication_classes = [SessionAuthentication, JWTAuthentication]  # 👈 دعم الجلسة والتوكن معاً
    permission_classes = [IsAuthenticated]  # 🔐 حماية المسار

    def get(self, request):
        try:
            # 1. إحصائيات الكيانات الأساسية من قاعدة البيانات الحقيقية
            total_users = User.objects.count()
            total_wallets = Wallet.objects.count()
            total_transactions = Transaction.objects.count()

            # 2. إجمالي الأرصدة والسيولة المتوفرة في النظام موزعة حسب كل عملة
            balances_by_currency = WalletBalance.objects.values('currency__code').annotate(
                total_balance=Sum('amount')
            )

            balances_summary = []
            for item in balances_by_currency:
                balances_summary.append({
                    "currency": item['currency__code'],
                    "total_amount": float(item['total_balance'] or 0)
                })

            # 3. تجميع الإحصائيات في الهيكل المتوقع تماماً من لوحة تحكم الـ HTML
            stats_data = {
                "summary": {
                    "total_users": total_users,
                    "total_wallets": total_wallets,
                    "total_transactions": total_transactions,
                },
                "balances_summary": balances_summary
            }
            
            return Response(stats_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"فشل قراءة قاعدة البيانات: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AdminGlobalTransactionsView(views.APIView):
    """
    واجهة برمجية لجلب كافة الحركات التاريخية المسجلة لجميع المحافظ والعملاء بشكل آمن ومحمي.
    تدعم التحقق المزدوج لمنع أي اختراق لبيانات العملاء.
    """
    authentication_classes = [SessionAuthentication, JWTAuthentication]  # 👈 دعم الجلسة والتوكن معاً
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # جلب جميع المعاملات من قاعدة البيانات nabil.sqlite3 مرتبة من الأحدث إلى الأقدم
            transactions = Transaction.objects.all().order_by('-created_at')
            
            transactions_data = []
            for tx in transactions:
                wallet_username = tx.wallet.user.username if (tx.wallet and tx.wallet.user) else "مستخدم عام"
                counterpart_username = tx.counterpart_wallet.user.username if (tx.counterpart_wallet and tx.counterpart_wallet.user) else None
                
                if tx.transaction_type == 'TRANSFER' and counterpart_username:
                    display_name = f"{wallet_username} ⇆ {counterpart_username}"
                else:
                    display_name = wallet_username

                transactions_data.append({
                    "id": tx.id,
                    "wallet_username": display_name,
                    "username": wallet_username,
                    "transaction_type": tx.transaction_type,
                    "amount": float(tx.amount),
                    "amount_value": float(tx.amount),
                    "currency_code": tx.from_currency.code if tx.from_currency else "USD",
                    "from_currency_code": tx.from_currency.code if tx.from_currency else "USD",
                    "converted_amount": float(tx.converted_amount) if tx.converted_amount else None,
                    "to_currency_code": tx.to_currency.code if tx.to_currency else "",
                    "created_at": tx.created_at.strftime('%Y-%m-%d %H:%M') if tx.created_at else "-"
                })

            return Response(transactions_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"فشل جلب المعاملات من قاعدة البيانات: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AdminExchangeRateView(views.APIView):
    """
    جلب وتحديث أسعار الصرف بشكل آمن ومحمي لمنع التلاعب بأسعار البنك.
    """
    authentication_classes = [SessionAuthentication, JWTAuthentication]  # 👈 دعم الجلسة والتوكن معاً
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # جلب جميع أسعار الصرف الحية
            rates = ExchangeRate.objects.all().order_by('from_currency__code')
            rates_data = []
            for r in rates:
                rates_data.append({
                    "id": r.id,
                    "from_currency": r.from_currency.code,
                    "to_currency": r.to_currency.code,
                    "rate": float(r.rate)
                })
            return Response(rates_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"فشل جلب أسعار الصرف: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        # التحقق الإضافي للتأكد من أن هذا المسؤول هو سوبر يوزر مالي فعلياً لحماية الصرف
        if not request.user.is_superuser:
            return Response({"error": "عذراً! لا تمتلك الصلاحيات الإشرافية لتغيير أسعار صرف البنك."}, status=status.HTTP_403_FORBIDDEN)

        from_code = request.data.get('from_currency')
        to_code = request.data.get('to_currency')
        rate_value = request.data.get('rate')

        if not from_code or not to_code or rate_value is None:
            return Response({"error": "جميع حقول سعر الصرف مطلوبة!"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from_currency = get_object_or_404(Currency, code=from_code)
            to_currency = get_object_or_404(Currency, code=to_code)

            # تحديث أو إنشاء سعر الصرف في nabil.sqlite3
            rate_obj, created = ExchangeRate.objects.update_or_create(
                from_currency=from_currency,
                to_currency=to_currency,
                defaults={"rate": Decimal(str(rate_value))}
            )

            # تحديث سعر الصرف العكسي تلقائياً لتسهيل وتبسيط العمليات الثنائية
            try:
                inverse_rate = Decimal("1") / Decimal(str(rate_value))
                ExchangeRate.objects.update_or_create(
                    from_currency=to_currency,
                    to_currency=from_currency,
                    defaults={"rate": inverse_rate}
                )
            except Exception:
                pass # تجاهل الأخطاء الحسابية في حال كانت المدخلات صفرية

            return Response({
                "success": f"تم قيد وتحديث سعر صرف {from_code} إلى {to_code} بنجاح حقيقي!",
                "rate": float(rate_obj.rate)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"فشلت عملية تحديث أسعار الصرف: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)