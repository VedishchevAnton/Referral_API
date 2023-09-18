from typing import Dict, Any

from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField

from users.models import User, AuthCode
from users.service import auth_code_age_validator
from users.utils import generate_referral_code
from rest_framework.exceptions import ValidationError


class LoginSerializer(serializers.ModelSerializer):
    """
    Сериализатор  предназначен для сериализации и десериализации объектов при отправке запросов к LoginView.
     Он используется для создания пользователей и генерации 4-значного цифрового токена для аутентификации.
    """
    # Определяем поле phone_number как обязательное
    # и используем PhoneNumberField для проверки корректности введенного номера телефона.
    phone_number = PhoneNumberField(required=True)

    class Meta:
        # Определяем модель, которая будет сериализована и десериализована,
        # а также поля, которые будут доступны для чтения и записи.
        model = User
        # Определяем поля, которые могут быть только для чтения.
        read_only_fields = ("id",)
        # Определяем поля, которые могут быть записаны и прочитаны.
        fields = ("id", "phone_number")

    def create(self, validated_data: dict) -> User:
        """
        Метод переопределяет метод create базового класса.
        Получает объект пользователя из базы данных, если он существует, иначе создает нового пользователя.
        Генерирует промо-код, если он не был создан ранее.
        Создает объект кода аутентификации и сохраняет его.
        Возвращает объект пользователя.
        """
        # Получаем объект пользователя из базы данных, если он существует, иначе создаем нового пользователя.
        instance, _ = User.objects.get_or_create(**validated_data)

        # Генерируем промо-код, если он не был создан ранее.
        if instance.referral_code is None:
            instance.referral_code = generate_referral_code()
            instance.save()

        # Создаем объект кода аутентификации и сохраняем его.
        code = AuthCode.objects.create(user=instance)
        code.save()

        # Возвращаем объект пользователя.
        return instance


class AuthCodeField(serializers.CharField):
    """
    AuthCodeField — это класс поля сериализатора,
    который расширяет класс поля сериализатора CharField из модуля rest_framework.serializers.
    Он используется для проверки длины и срока использования кода активации.
    """

    # Словарь сообщений об ошибках по умолчанию
    default_error_messages = {
        'required': 'Неверный код',
        'invalid': 'Неверный код',
    }

    def validate(self, value):
        """
        Проверяет возраст кода активации.
        :param value: код активации
        :return: код активации, если он проходит проверку
        :raises serializers.ValidationError: если код не проходит проверку
        """
        # Вызов метода validate() базового класса
        super().validate(value)
        # Проверка возраста кода активации
        if not auth_code_age_validator(value):
            raise serializers.ValidationError(self.error_messages['invalid'])
        return value


class VerificationAuthCodeSerializer(serializers.Serializer):
    """
    VerificationAuthCodeSerializer — это класс сериализатора,
    который наследуется от класса Serializer из модуля rest_framework.serializers.
    Он предназначен для сериализации и десериализации объектов при обработке запроса AuthCodeField.
    """
    phone_number = PhoneNumberField(required=False, max_length=17)
    code = AuthCodeField(min_length=4, max_length=4, validators=[auth_code_age_validator])

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Метод переопределяет метод класса. Принимает в качестве параметров объект в виде словаря.
        Выполняет проверку полученных данных, дополняет их и возвращает в виде словаря.
        :param: Attrs: Словарь, содержащий данные аутентификации пользователя.
        :return:  Словарь, содержащий информацию о пользователе.
        """
        code = attrs.get('code', None)
        phone_number = attrs.get('phone_number', None)
        if code is None or phone_number is None:
            raise serializers.ValidationError('Не предоставлены данные аутентификации пользователя.')
        try:
            user = User.objects.get(phone_number=phone_number)
            AuthCode.objects.filter(user=user, code=code, is_active=True).first()
            attrs['user'] = user
            user.is_verified = True
            user.save()

            if not user.is_active:
                raise serializers.ValidationError('Учетная запись пользователя отключена.')

        except AuthCode.DoesNotExist:
            raise serializers.ValidationError('Введен неверный токен')
        except User.DoesNotExist:
            raise serializers.ValidationError('Предоставлен неверный пользователь.')
        except ValidationError:
            raise serializers.ValidationError('Предоставлены неверные параметры.')
        else:
            return attrs


class TokenResponseSerializer(serializers.Serializer):
    """
    Сериализатор AuthCodeResponseSerializer используется для сериализации кода подтверждения авторизации.
    Он преобразует код в строку и возвращает его в ответе на запрос.
    Он используется для возврата ключа кода в ответе на запрос проверки кода активации,
    который был отправлен пользователю для подтверждения его номера телефона.
    Код используется для подтверждения, что пользователь является владельцем номера телефона,
    и после подтверждения, пользователь получает доступ к приложению.
    """
    token = serializers.CharField(source='key')
    key = serializers.CharField(write_only=True)


class ProfileForeignSerializer(serializers.ModelSerializer):
    """
    Сериализатор ProfileForeignSerializer используется для сериализации объектов модели User,
     возвращая только поле phone_number.
    Этот сериализатор используется вместе с представлениями DRF для создания API, которые возвращают
    только определенные поля модели User в ответ на запросы клиентов.
    """

    class Meta:
        model = User
        fields = ['phone_number', ]


class ProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для удобной сериализации и десериализации объектов
    при выполнении запросов к ProfileView с использованием методов GET и PATCH.

    """
    unentered_referral_code = serializers.CharField(write_only=True)
    entered_referral_code = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'phone_number', 'referral_code', 'first_name', 'last_name',
                  'email', 'unentered_referral_code', 'entered_referral_code']

    def get_entered_referral_code(self, obj: User) -> list:
        """
        Функция создает набор запросов из связанных
        экземпляров классов и сериализует их для удобного отображения.
        """
        # Получаем queryset пользователей, которые ввели промо-код, связанный с переданным объектом User
        queryset = User.objects.filter(referred_by=obj)
        return [ProfileForeignSerializer(q).data for q in queryset]

    def update(self, request, *args, **kwargs):
        """
        Функция используется для обновления экземпляра класса ProfileSerializer.
        Она устанавливает атрибут partial в значение True, что позволяет делать частичные обновления экземпляра.
        Затем она вызывает метод is_valid для проверки экземпляра на валидность.
        Если raise_exception установлен в True, будет вызвано исключение, если экземпляр не является действительным.
        Наконец, она вызывает метод update родительского класса для обновления экземпляра с проверенными данными.
        """
        self.partial = True
        self.is_valid(raise_exception=True)  # вызываем метод is_valid()
        return super().update(request, *args, **kwargs)

    def is_valid(self, *, raise_exception=False) -> bool:
        """
        Проверяет, является ли объект сериализатора действительным.
        Если при создании или обновлении профиля пользователя был введен промо-код,
        то метод проверяет его наличие в базе данных и связывает пользователя с введенным кодом.
        Затем метод вызывает метод is_valid базового класса.
        :param raise_exception: Если True, то исключение будет вызвано при обнаружении ошибки валидации.
        :return: True, если объект сериализатора действительный, иначе False.
        """
        # * - все аргументы после него должны быть переданы в виде именованных аргументов, а не позиционных.
        # Получаем введенный код приглашения
        referred_by = self.initial_data.get('unentered_referral_code', None)
        # Если промо-код был введен
        if referred_by is not None:
            # Если пользователь уже связан с другим промо-кодом, вызываем исключение
            if self.instance.referred_by is not None:
                raise serializers.ValidationError('Вы можете активировать промо-код только один раз.')
            else:
                # Ищем пользователя с введенным промо-кодом
                try:
                    user_with_refered = User.objects.get(referral_code=referred_by)
                except User.DoesNotExist:
                    # Если пользователь не найден, вызываем исключение
                    raise serializers.ValidationError('Введен неверный код.')
                else:
                    # Связываем пользователя с введенным промо-кодом
                    self.instance.referred_by = user_with_refered
                    self.instance.save()

        return super().is_valid(raise_exception=raise_exception)
    # raise_exception - это параметр метода is_valid(),
    # который отвечает за выброс исключения в случае невалидности данных.
    # Если параметр raise_exception установлен в True, то метод is_valid() выбросит исключение ValidationError,
    # если данные не прошли валидацию
