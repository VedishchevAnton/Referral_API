from django.utils import timezone
from django.conf import settings

from users.models import AuthCode


def auth_code_age_validator(code) -> bool:
    """
    Метод auth_code_age_validator - это валидатор для проверки возраста использования кода подтверждения.
    Принимает значение кода в качестве параметра. По истечении срока использования код становится не действительным.
    :return:- bool: True, если токен активен и не истек, иначе False
    """
    try:
        auth_code = AuthCode.objects.filter(code=code, is_active=True).first()
        seconds = (timezone.now() - auth_code.created_at).total_seconds()
        if seconds <= settings.CODE_EXPIRE_TIME:  # срок жизни кода подверждения 10 минут
            return True
        else:
            # Код становится не действительным.
            auth_code.is_active = False
            auth_code.save()
            return False

    except AuthCode.DoesNotExist:
        # Нет действительного кода.
        return False
