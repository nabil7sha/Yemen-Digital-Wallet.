from rest_framework import status, views, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction

from .models import Profile, Wallet, WalletBalance, Currency
from .auth_serializers import RegisterSerializer, ProfileSerializer

class RegisterView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        phone_number = serializer.validated_data.get('phone_number', '')

        # استخدام atomic لضمان بناء الحساب والمحفظة والملف معاً أو فشل العملية بالكامل
        with transaction.atomic():
            # 1. إنشاء المستخدم الأساسي وتشفير كلمة المرور
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # 2. إنشاء الملف الشخصي المرتبط به
            Profile.objects.create(user=user, phone_number=phone_number)
            
            # 3. إنشاء المحفظة الرقمية الخاصة به تلقائياً
            wallet = Wallet.objects.create(user=user)
            
            # 4. خطوة اختيارية (Pro-tip): إنشاء أرصدة أولية صفرية للعملات الأساسية النشطة إن وجدت
            active_currencies = Currency.objects.filter(is_active=True)
            for currency in active_currencies:
                WalletBalance.objects.create(wallet=wallet, currency=currency, amount=0.00)
            
            # 5. توليد مفتاح التوثيق (Token) للمستخدم الجديد مباشرة
            token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "message": "تم إنشاء الحساب والمحفظة بنجاح.",
            "token": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({"error": "يرجى تزويدنا باسم المستخدم وكلمة المرور."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if not user:
            return Response({"error": "بيانات الدخول غير صحيحة."}, status=status.HTTP_401_UNAUTHORIZED)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "message": "تم تسجيل الدخول بنجاح."
        }, status=status.HTTP_200_OK)


class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # حذف الـ Token الخاص بالمستخدم لإبطال جلسة العمل الحالية
        request.user.auth_token.delete()
        return Response({"message": "تم تسجيل الخروج بنجاح وتدمير الجلسة."}, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/profile -> لعرض الملف الشخصي للمستخدم الحالي
    PUT /api/profile -> لتحديث بيانات الملف الشخصي (مثل رقم الهاتف)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        # ضمان إرجاع الملف الشخصي الخاص بالمستخدم المصادق عليه فقط
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile