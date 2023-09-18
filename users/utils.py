import random
import string

from rest_framework.authtoken.models import Token


def generate_referral_code():
    """
    Метод генерирует промо код, состоящий из 6 символов, включая заглавные буквы и цифры.
    :return: Строка, содержащая 6 символов, включая заглавные буквы и цифры.
    """
    return ''.join([random.choice(list(string.ascii_uppercase + string.digits)) for x in range(6)])


def generate_auth_code():
    """
    Метод генерирует код активации из 4 цифр.
    :return: Строка, содержащая 4 цифры.
    """
    return ''.join([random.choice(list('123456789')) for x in range(4)])


def sms_with_auth_code(user, auth_code, **kwargs) -> None:
    """
    :param:user - экземпляр пользователя;
    - confirmation_token - токен подтверждения;
    - **kwargs - именованные аргументы.
    При вызове функция отправляет SMS с кодом подтверждения авторизации на номер телефона пользователя.
    В настоящее время функция заменена заглушкой, которая выводит код подтверждения на консоль.
    :return: None функция заменена заглушкой, которая выводит код подтверждения на консоль.
    """
    print(f'На телефонный номер {user.phone_number} отправлен код подтверждения авторизации {auth_code}')


def create_auth_token(user) -> Token:
    """
    Функция создает экземпляр класса Token для аутентификации пользователя с помощью токена.
    Возвращает созданный экземпляр.
    :param:- user: экземпляр пользователя
    :return: - созданный экземпляр Token
    """
    return Token.objects.get_or_create(user=user)[0]
