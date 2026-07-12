from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

from .models import Transaction, Notification
from .history_serializers import TransactionDetailSerializer, NotificationSerializer

class TransactionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionDetailSerializer

    def get_queryset(self):
        user = self.request.user
        # تحسين الأداء عبر select_related لجلب بيانات الجداول المرتبطة بـ Query واحد فقط
        # جلب المعاملات التي يكون فيها المستخدم هو المرسل (wallet) أو المستقبل (counterpart_wallet)
        return Transaction.objects.select_related(
            'wallet__user', 
            'counterpart_wallet__user', 
            'from_currency', 
            'to_currency'
        ).filter(
            Q(wallet__user=user) | Q(counterpart_wallet__user=user)
        ).order_by('-created_at') # ترتيب من الأحدث إلى الأقدم


class TransactionDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionDetailSerializer

    def get_queryset(self):
        user = self.request.user
        # تأمين جلب المعاملة الخاصة بالمستخدم نفسه فقط لمنع أي مستخدم من رؤية معاملات غيره
        return Transaction.objects.select_related(
            'wallet__user', 
            'counterpart_wallet__user', 
            'from_currency', 
            'to_currency'
        ).filter(
            Q(wallet__user=user) | Q(counterpart_wallet__user=user)
        )


class NotificationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        # جلب الإشعارات الخاصة بالمستخدم الحالي فقط مرتبة من الأحدث للأقدم
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class MarkNotificationsReadView(APIView):
    """
    نقطة وصول إضافية مساعدة لتحديث الإشعارات وجعلها 'مقروءة' بمجرد فتحها
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"message": "تم تحديد جميع الإشعارات كمقروءة."}, status=status.HTTP_200_OK)