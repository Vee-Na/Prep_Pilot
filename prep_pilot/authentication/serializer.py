from django.contrib.auth import get_user_model
from rest_framework import serializers

Profile = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Profile
        fields = ['id', 'email', 'username', 'first_name', 'password']

    def validate_email(self, value):
        value = value.lower()
        if Profile.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Email already registered.')
        return value

    def validate_username(self, value):
        if '@' in value:
            raise serializers.ValidationError("Username cannot contain '@'.")
        return value

    def create(self, validated_data):
        
        return Profile.objects.create_user(**validated_data)