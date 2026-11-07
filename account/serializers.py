from rest_framework import serializers
from user.models import User
from django.core.mail import send_mail
from django.core.signing import TimestampSigner

signer = TimestampSigner()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=128,
        min_length=6,
        write_only=True
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'password')

        read_only_fields = ('token',)


class EditAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "avatar")
        extra_kwargs = {
            "email": {"required": False},
            "avatar": {"required": False},
        }

    def validate_email(self, value):
        user = self.context["request"].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError('This email address is used')
        return value

    def update(self, instance, validated_data):
        new_email = validated_data.pop("email", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if new_email and new_email != instance.email:
            self._send_email_confirmation(instance, new_email)

        return instance

    def _send_email_confirmation(self, user, new_email):
        token = signer.sign(f"{user.pk}:{new_email}")

        confirm_url = f"http://127.0.0.1:8000/api/v1/account/confirm-email?token={token}"

        send_mail(
            subject="Confirm your new email",
            message=f"Click the link to confirm the new email:\n{confirm_url}",
            from_email=None,
            recipient_list=[new_email],
        )
