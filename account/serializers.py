import uuid
from rest_framework import serializers
from user.models import User
from django.core.mail import send_mail
from django.core.signing import TimestampSigner
from io import BytesIO
from PIL import Image, ImageFilter
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

signer = TimestampSigner()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=128,
        min_length=6,
        write_only=True
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'password', 'avatar', 'avatar_50', 'avatar_200')

        read_only_fields = ('token',)


class EditAccountSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, write_only=True)
    avatar_50 = serializers.SerializerMethodField()
    avatar_200 = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'avatar', 'avatar_50', 'avatar_200')
        extra_kwargs = {
            "avatar": {"required": False},
        }

    def get_avatar_50(self, obj):
        if not obj.avatar:
            return None
        return f"/media/avatars/{obj.avatar}_50.jpg"

    def get_avatar_200(self, obj):
        if not obj.avatar:
            return None
        return f"/media/avatars/{obj.avatar}_200.jpg"

    def validate_email(self, value):
        user = self.context["request"].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError('This email address is used')
        return value

    def update(self, instance, validated_data):
        new_email = validated_data.pop("email")
        avatar_file = validated_data.pop("avatar", None)

        if avatar_file:
            self._save_avatars(instance, avatar_file)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if new_email != instance.email:
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

    def _save_avatars(self, user, uploaded_file):
        if user.avatar:
            old_base = user.avatar
            for size, ext in [("50", "png"), ("200", "png")]:
                old_path = f"avatars/{old_base}_{size}.{ext}"
                if default_storage.exists(old_path):
                    default_storage.delete(old_path)

        base_name = str(uuid.uuid4())
        img = Image.open(uploaded_file).convert("RGB")

        width, height = img.size
        min_side = min(width, height)
        left = (width - min_side) // 2
        top = (height - min_side) // 2
        img = img.crop((left, top, left + min_side, top + min_side))

        sizes = {
            "50": (50, 50),
            "200": (200, 200),
        }

        for size_key, dimensions in sizes.items():
            temp = img.resize(
                (dimensions[0] * 2, dimensions[1] * 2),
                Image.Resampling.LANCZOS
            )
            resized = temp.resize(dimensions, Image.Resampling.LANCZOS)
            resized = resized.filter(ImageFilter.SHARPEN)

            buffer = BytesIO()
            if size_key == "50":
                resized.save(buffer, format="PNG", quality=95, optimize=True)
                ext = "png"
            else:
                resized.save(buffer, format="PNG", quality=95, optimize=True)
                ext = "png"

            buffer.seek(0)
            filename = f"avatars/{base_name}_{size_key}.{ext}"
            default_storage.save(filename, ContentFile(buffer.read()))

        user.avatar = base_name
