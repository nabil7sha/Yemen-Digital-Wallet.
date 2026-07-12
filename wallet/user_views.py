from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction
from decimal import Decimal
from .models import Wallet, WalletBalance, Transaction, Currency, ExchangeRate

class UserTransactionView(views.APIView):
    permission_classes = [AllowAny]  # متاح للتبسيط، يفضل لاحقاً ربطه بـ IsAuthenticated

    def post(self, request):
        action_type = request.data.get('action_type')  # 'TRANSFER' أو 'EXCHANGE'
        username = request.data.get('username')  # اسم المستخدم الحالي (المنفّذ)
        amount = Decimal(str(request.data.get('amount', 0)))
        from_currency_code = request.data.get('from_currency')

        if amount <= 0:
            return Response({"error": "المبلغ يجب أن يكون أكبر من الصفر"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # 1. جلب محفظة المستخدم الحالي والعملة الأساسية
                user_wallet = Wallet.objects.get(user__username=username)
                from_currency = Currency.objects.get(code=from_currency_code, is_active=True)
                
                # جلب رصيد العملة الأساسية للمستخدم
                user_balance, _ = WalletBalance.objects.get_or_create(wallet=user_wallet, currency=from_currency)

                if user_balance.amount < amount:
                    return Response({"error": "رصيد غير كافٍ لإتمام العملية"}, status=status.HTTP_400_BAD_REQUEST)

                # ----------------- حالة التحويل -----------------
                if action_type == 'TRANSFER':
                    counterpart_username = request.data.get('counterpart_username')
                    if username == counterpart_username:
                        return Response({"error": "لا يمكنك التحويل لنفس محفظتك"}, status=status.HTTP_400_BAD_REQUEST)

                    receiver_wallet = Wallet.objects.get(user__username=counterpart_username)
                    receiver_balance, _ = WalletBalance.objects.get_or_create(wallet=receiver_wallet, currency=from_currency)

                    # الخصم والإضافة بنفس العملة
                    user_balance.amount -= amount
                    receiver_balance.amount += amount
                    user_balance.save()
                    receiver_balance.save()

                    # تسجيل العملية
                    tx = Transaction.objects.create(
                        wallet=user_wallet,
                        counterpart_wallet=receiver_wallet,
                        transaction_type='TRANSFER',
                        from_currency=from_currency,
                        amount=amount
                    )
                    return Response({"message": f"تم تحويل {amount} {from_currency_code} بنجاح إلى {counterpart_username}"}, status=status.HTTP_200_OK)

                # ----------------- حالة المصارفة -----------------
                elif action_type == 'EXCHANGE':
                    to_currency_code = request.data.get('to_currency')
                    if from_currency_code == to_currency_code:
                        return Response({"error": "لا يمكن مصارفة العملة لنفسها"}, status=status.HTTP_400_BAD_REQUEST)

                    to_currency = Currency.objects.get(code=to_currency_code, is_active=True)
                    
                    # جلب سعر الصرف
                    try:
                        rate_obj = ExchangeRate.objects.get(from_currency=from_currency, to_currency=to_currency)
                        rate = rate_obj.rate
                    except ExchangeRate.DoesNotExist:
                        return Response({"error": f"سعر الصرف من {from_currency_code} إلى {to_currency_code} غير متوفر"}, status=status.HTTP_400_BAD_REQUEST)

                    converted_amount = amount * rate
                    target_balance, _ = WalletBalance.objects.get_or_create(wallet=user_wallet, currency=to_currency)

                    # الخصم من العملة الأولى والإضافة للعملة الثانية في نفس المحفظة
                    user_balance.amount -= amount
                    target_balance.amount += converted_amount
                    user_balance.save()
                    target_balance.save()

                    # تسجيل العملية
                    tx = Transaction.objects.create(
                        wallet=user_wallet,
                        transaction_type='EXCHANGE',
                        from_currency=from_currency,
                        to_currency=to_currency,
                        amount=amount,
                        converted_amount=converted_amount
                    )
                    return Response({"message": f"تم تحويل {amount} {from_currency_code} إلى {converted_amount:.2f} {to_currency_code} بنجاح"}, status=status.HTTP_200_OK)

                else:
                    return Response({"error": "نوع العملية غير مدعوم"}, status=status.HTTP_400_BAD_REQUEST)

        except Wallet.DoesNotExist:
            return Response({"error": "المحفظة أو اسم المستخدم غير موجود"}, status=status.HTTP_404_NOT_FOUND)
        except Currency.DoesNotExist:
            return Response({"error": "العملة المطلوبة غير مدعومة أو غير نشطة"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"حدث خطأ أثناء المعالجة: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)