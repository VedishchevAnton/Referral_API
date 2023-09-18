# Реферальная система


# Задание
Реализовать простую реферальную систему. Минимальный интерфейс для тестирования

Реализовать логику и API для следующего функционала :

Авторизация по номеру телефона. Первый запрос на ввод номера телефона. Имитировать отправку 4х значного кода авторизации(задержку на сервере 1-2 сек). Второй запрос на ввод кода.

Если пользователь ранее не авторизовывался, то записать его в бд.

Запрос на профиль пользователя.

Пользователю нужно при первой авторизации нужно присвоить рандомно сгенерированный 6-значный инвайт-код(цифры и символы).

В профиле у пользователя должна быть возможность ввести чужой инвайт-код(при вводе проверять на существование). В своем профиле можно активировать только 1 инвайт код, если пользователь уже когда-то активировал инвайт код, то нужно выводить его в соответсвующем поле в запросе на профиль пользователя.

В API профиля должен выводиться список пользователей(номеров телефона), которые ввели инвайт код текущего пользователя.

Реализовать и описать в readme Api для всего функционала.

Создать и прислать Postman коллекцию со всеми запросами.

Запуск проекта:

- Клонируйте репозиторий с проектом:  
  git clone

- В созданной директории установите виртуальное окружение, активируйте его и установите необходимые зависимости:
  python3 -m venv venv  
  venv/bin/activate    
  pip install -r requirements.txt  
- Создайте свою базу данных 
  psql -U postgres / CREATE DATABASE  
- Выполните миграции:
  python manage.py migrate

- Создайте суперпользователя:
  python manage.py createsuperuser

Запустите сервер:
python manage.py runserver

Ваш проект запустился на http://127.0.0.1:8000/
Коллекия запросов в файле Referral System API.postman_collection.json