from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Wallet

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['user', 'phone_number', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=15, required=False, write_only=True)
    password = serializers.CharField(write_only=True, min_length=6, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone_number']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("اسم المستخدم هذا مأخوذ بالفعل.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("هذا البريد الإلكتروني مسجل مسبقاً.")
        return value