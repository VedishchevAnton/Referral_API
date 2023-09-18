from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from time import sleep

from users.models import User, AuthCode
from users.serializers import LoginSerializer, VerificationAuthCodeSerializer, TokenResponseSerializer, \
    ProfileSerializer
from users.utils import sms_with_auth_code, create_auth_token


# Create your views here.
class LoginView(CreateAPIView):
    """
    Класс LoginView - это класс-представление, который обрабатывает POST-запросы по адресу "login/".
    Когда пользователь обращается к этому адресу, он получает данные из базы данных, если они доступны,
    создает новый экземпляр, отправляет 4-значный цифровой код для аутентификации.
    """
    queryset = User.objects.all()  # получаем все объекты модели User
    permission_classes = [AllowAny, ]  # разрешаем доступ всем пользователям
    serializer_class = LoginSerializer  # используем сериализатор LoginSerializer

    def post(self, request, *args, **kwargs) -> Response:
        """
        Функция post переопределяет метод родительского класса, чтобы обеспечить правильную обработку POST-запроса.
        Она реализует функционал поиска или создания пользователя по введенному номеру телефона,
        генерации 4-значного цифрового токена для подтверждения аутентификации
        и отправки его в виде SMS на введенный номер телефона.
        :param request: объект запроса
        :param args: дополнительные аргументы
        :param kwargs: дополнительные именованные аргументы
        :return: объект ответа
        """
        serializer = self.get_serializer(data=request.data)  # создаем экземпляр сериализатора
        serializer.is_valid(raise_exception=True)  # проверяем, что данные валидны
        serializer.save()  # сохраняем данные

        if serializer.is_valid:
            user = User.objects.get(pk=serializer.data['id'])  # получаем пользователя по id
            confirmation_token = AuthCode.objects.filter(
                user=user).first()  # получаем токен для обратного вызова
            sleep(2)  # имитация задержки на сервере
            sms_with_auth_code(user, confirmation_token, **kwargs)  # отправляем SMS с токеном

        data = {
            "user": serializer.data,
            "next_page": f"http://127.0.0.1:8000/verification/{serializer.data['id']}",
            "message": "SMS с токеном отправлено на указанный номер телефона",
        }

        return Response(data, status=status.HTTP_201_CREATED)


class VerificationTokenView(APIView):
    """
    Класс VerificationTokenView - это CBV для обработки POST-запроса к URL /verify/<int:pk>.
    Предоставляет проверку введенного токена подтверждения аутентификации и генерацию токена авторизации пользователя.
    """
    serializer_class = VerificationAuthCodeSerializer
    permission_classes = [AllowAny, ]

    def post(self, request, *args, **kwargs) -> Response:
        """
        Функция post переопределяет логику метода родительского класса. При вызове метода
        он вызывает проверку полученных данных с использованием сериализатора, создает или получает токен авторизации.
        При успешном выполнении он возвращает объект Response, содержащий токен авторизации;
        при недопустимых данных он возвращает объект Response, содержащий описание ошибки.
        :param request: объект запроса
        :param args: дополнительные аргументы
        :param kwargs: дополнительные именованные аргументы
        :return: объект Response
        """
        # Создаем экземпляр сериализатора и передаем ему полученные данные
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # Получаем пользователя из сериализатора
            user = serializer.validated_data['user']
            # Создаем или получаем токен авторизации для пользователя
            auth_token = create_auth_token(user)

            if auth_token:
                # Создаем экземпляр сериализатора для токена авторизации и передаем ему данные
                token_serializer = TokenResponseSerializer(data={"token": auth_token.key, }, partial=True)
                if token_serializer.is_valid():
                    # Возвращаем наш ключ для использования.
                    return Response(token_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Не удалось войти. Попробуйте позже.'},
                                status=status.HTTP_400_BAD_REQUEST)


class ProfileView(RetrieveUpdateAPIView):
    """
    Класс ProfileView является классом-представлением (CBV) для обработки GET и PATCH запросов,
    отправленных по URL-адресу '/profile/'.
    Он позволяет просматривать профиль текущего пользователя и изменять его данные, а также содержит функциональность,
    которая обеспечивает ввод промо-кода.
    """
    queryset = User.objects.filter(is_active=True)
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, ]

    def get_object(self) -> User:
        """
        Функция переопределяет метод родительского класса, заменяет логику получения объекта
        работы методов. Позволяет представлению работать без явного указания объекта
        в качестве параметра URL. Ограничивает доступ к профилям других пользователей. При вызове
        метод не принимает никаких других параметров, кроме собственного экземпляра класса.
        :return: экземпляр авторизованного пользователя, сделавшего запрос.
        """
        return self.request.user
