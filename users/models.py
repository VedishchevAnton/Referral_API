from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from users.utils import generate_referral_code, generate_auth_code


# Create your models here.
class CustomUserManager(BaseUserManager):
    """
       Класс CustomUserManager наследует класс BaseUserManager из модуля django.contrib.auth.base_user.
       Он переопределяет его функциональность для корректной работы приложения.
       """
    use_in_migrations = True  # атрибут класса, который указывает, что этот менеджер должен использоваться в миграциях.

    def create_user(self, phone_number: str, **extra_fields):
        """
        Метод класса, который переопределяет метод базового класса.
        Он получает или создает объект пользователя, если его нет в базе данных, и возвращает объект пользователя.
        """
        if not phone_number:
            raise ValueError('Необходимо указать телефон')

        user, created = User.objects.get_or_create(phone_number=phone_number)

        if user.referral_code is None:  # проверяем есть ли промо-код
            user.referral_code = generate_referral_code()
            user.save()
        code = AuthCode.objects.create(user=user)
        code.save()

        return user

    def create_superuser(self, phone_number: str, **extra_fields):
        """
        Метод класса, который создает суперпользователя по номеру телефона и паролю.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        user = self.create_user(phone_number, **extra_fields)
        user.is_staff = extra_fields['is_staff']
        user.is_superuser = extra_fields['is_superuser']
        user.save()

        return user


class User(AbstractUser):
    username = None
    password = None
    phone_number = PhoneNumberField(unique=True, verbose_name='Номер телефона')  # формат E.164
    referral_code = models.CharField(max_length=6, null=True, default=None, verbose_name='Промо-код')
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='referrals', verbose_name='Приглашенный пользователь')  # ссылка на
    # пользователя, который пригласил данного пользователя в приложение.
    is_verified = models.BooleanField(default=False, verbose_name='Верифицированный пользователь')

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return str(self.phone_number)


class AuthCode(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    is_active = models.BooleanField(default=True, verbose_name='Флаг активности')
    code = models.CharField(max_length=4, default=generate_auth_code, verbose_name='Код активации')

    class Meta:
        verbose_name = 'Код активации'
        verbose_name_plural = 'Коды активации'
        ordering = ['-id']

    def __str__(self):
        return f'{self.code}'
