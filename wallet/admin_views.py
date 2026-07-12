from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny  # السماح بالوصول العام بدون تعقيدات أمنية وتوكن
from django.contrib.auth.models import User
from django.db.models import Sum
from .models import Wallet, WalletBalance, Transaction, Currency

class AdminDashboardStatsView(views.APIView):
    """
    واجهة برمجية لجلب إحصائيات قاعدة البيانات (nabil.sqlite3) العامة بشكل حي ومباشر
    """
    permission_classes = [AllowAny]  # عرض مباشر وبدون حماية توثيق

    def get(self, request):
        try:
            # 1. إحصائيات الكيانات الأساسية
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
    واجهة برمجية لجلب كافة الحركات التاريخية المسجلة لجميع المحافظ والعملاء حياً ومباشراً
    """
    permission_classes = [AllowAny]  # عرض مباشر وبدون حماية توثيق

    def get(self, request):
        try:
            # جلب جميع المعاملات من الأحدث إلى الأقدم
            transactions = Transaction.objects.all().order_by('-created_at')
            
            transactions_data = []
            for tx in transactions:
                # جلب اسم صاحب المحفظة
                wallet_username = tx.wallet.user.username if (tx.wallet and tx.wallet.user) else "مستخدم عام"
                
                # جلب الطرف المقابل في حال التحويل المالي
                counterpart_username = tx.counterpart_wallet.user.username if (tx.counterpart_wallet and tx.counterpart_wallet.user) else None
                
                # تنسيق الاسم المعروض لتوضيح أطراف عملية التحويل
                if tx.transaction_type == 'TRANSFER' and counterpart_username:
                    display_name = f"{wallet_username} ⇆ {counterpart_username}"
                else:
                    display_name = wallet_username

                # تنسيق العمليات بمرونة تامة لتطابق حقول الـ HTML
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