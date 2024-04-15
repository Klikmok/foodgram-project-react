# Foodrgam
### Foodgram - проект для создания рецептов. Пользователи могут подписываться на понравившихся авторов, добавлять рецепты в избранное и список рецпетов. Есть возможность скачать список ингредиентов, необходимых для приготовления блюд из списка рецпетов
# Подготовка и запуск проекта
## Склонировать репозиторий из GitHub:
```
git clone git@github.com:klikmok/foodgram-project-react.git
```
## Для работы с удаленным сервером (на ubuntu):
* Выполните вход на свой удаленный сервер

* Установите docker на сервер через утилиту apt:
```
sudo apt install docker.io 
```
* Установите docker-compose на сервер:
```
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```
* Локально отредактируйте файл infra/nginx.conf и в строке server_name впишите свой IP
* Скопируйте файлы docker-compose.yml и nginx.conf из директории infra на сервер:
```
scp docker-compose.yml <username>@<host>:/home/<username>/docker-compose.yml
scp nginx.conf <username>@<host>:/home/<username>/nginx.conf
```

* Cоздайте .env файл и впишите:
    ```
    DB_ENGINE=<django.db.backends.postgresql>
    DB_NAME=<имя базы данных postgres>
    DB_USER=<пользователь бд>
    DB_PASSWORD=<пароль>
    DB_HOST=<db>
    DB_PORT=<5432>
    SECRET_KEY=<секретный ключ проекта django>
    ```
* Для работы с GitActions добавьте в Secrets GitHub переменные окружения для работы:
    ```
    # Также укажите все те же переменные, которые были указаны в .env!
    
    DOCKER_PASSWORD=<пароль от DockerHub>
    DOCKER_USERNAME=<имя пользователя>
    
    SECRET_KEY=<секретный ключ проекта django>

    USER=<username для подключения к серверу>
    HOST=<IP сервера>
    PASSPHRASE=<пароль для сервера, если он установлен>
    SSH_KEY=<ваш SSH ключ (для получения команда: cat ~/.ssh/id_rsa)>

    TELEGRAM_TO=<ID чата, в который придет сообщение>
    TELEGRAM_TOKEN=<токен вашего бота>
    # Токены телеграма можно получить с помощью ботов BotFather(для бота), и UserInfoBot(для айди чата)
    ```
    Запуск Workflow состоит из трёх шагов:
     - Проверка кода на соответствие Flake8 и Flake8-isort
     - Сборка и публикация образа бэкенда на DockerHub.
     - Автоматический деплой на удаленный сервер.
     - Отправка уведомления вам в телеграм.  
  
* На сервере соберите docker-compose:
```
sudo docker-compose up -d --build
```
* После успешной сборки на сервере выполните команды (только после первого деплоя):
    - Соберите статические файлы:
    ```
    sudo docker-compose exec backend python manage.py collectstatic
    ```
    - Примените миграции:
    ```
    sudo docker-compose exec backend python manage.py migrate
    ```
    - Загрузите ингридиенты  в базу данных (необязательно):  
    ```
    sudo docker-compose exec backend python manage.py load_data
    ```
    - Создать суперпользователя Django:
    ```
    sudo docker-compose exec backend python manage.py createsuperuser
    ```
    - Проект будет доступен по IP вашего удаленного сервера
## Проект заупущен, и функционирует по адресу:
### https://foodgram.servecounterstrike.com/recipes

# Бекэнд и девопс проекта выполнил [Рыбаков Алексей](https://github.com/Klikmok)