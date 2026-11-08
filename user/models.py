import jwt

from datetime import datetime, timedelta
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)
from django.db import models
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name, email, password=None):
        if first_name is None:
            raise TypeError('Users must have a first name.')

        if last_name is None:
            raise TypeError('Users must have a last name.')

        if email is None:
            raise TypeError('Users must have an email address.')

        user = self.model(first_name=first_name, last_name=last_name, email=self.normalize_email(email))
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, first_name, last_name, email, password):
        if password is None:
            raise TypeError('Superusers must have a password.')

        user = self.create_user(first_name, last_name, email, password)
        user.is_superuser = True
        user.is_staff = True
        user.role = User.Role.ADMIN
        user.save()

        return user


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        TEACHER = "teacher", "Teacher"
        STUDENT = "student", "Student"
        ADMIN = "admin", "Admin"

    username = None
    first_name = models.CharField( max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(db_index=True, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=20,choices=Role.choices, default=Role.STUDENT)
    avatar = models.CharField(max_length=100, blank=True, null=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def token(self):
        return self._generate_jwt_token()

    @property
    def avatar_50(self):
        if not self.avatar:
            return None
        return f"/media/avatars/{self.avatar}_50.jpg"

    @property
    def avatar_200(self):
        if not self.avatar:
            return None
        return f"/media/avatars/{self.avatar}_200.jpg"

    def get_full_name(self):
        return self.first_name + ' ' + self.last_name

    def get_short_name(self):
        return self.email

    def _generate_jwt_token(self):
        dt = datetime.now() + timedelta(days=1)

        return jwt.encode({
            'id': self.id,
            'exp': int(dt.strftime('%s'))
        }, settings.SECRET_KEY, algorithm='HS256')
