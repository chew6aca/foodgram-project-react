# Foodgram - сервис для размещения рецептов блюд.
Данный проект является площадкой, на которой пользователи могут регистрироваться,
размещать различные рецепты блюд, подписываться на других авторов, чтобы отслеживать
размещаемые ими рецепты, добавлять рецепты в избранное. Также можно формировать список
покупок: сервис суммирует все необходимые ингредиенты для выбранных рецептов и выдаёт
список в виде текстового документа.
### Сервис доступен по адресу
https://foodgram1516.ddns.net
## Как запустить проект
## Локально
Склонировать репозиторий
```
git clone https://github.com/chew6aca/foodgram-project-react.git
```
В директории infra/ создать и заполнить файл .env в соответствии с примером
```
POSTGRES_DB=some_name
POSTGRES_USER=some_user
POSTGRES_PASSWORD=some_password
DB_NAME=db_name
DB_PORT=5432
DB_HOST=db
SECRET_KEY=django_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1:localhost
DB_POSTGRES=True
```
Из директории /infra выполнить команду
```
docker compose up -d
```
Приложение будет доступно по адресу
```
 http://localhost/
```
а документация
```
 http://localhost/api/docs/
```
## На удалённом сервере
Если на сервере не установлен docker, последовательно выполнить команды
```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin
```
Создать директорию проекта, создать в ней следующие файлы и скопировать в них содержимое соответсвующих локальных файлов.
```
.env
nginx.conf
docker-compose.yml
```
Из директории проекта выполнить команду
```
sudo docker compose up -d
```
Выполнить миграции
```
sudo docker compose exec backend python manage.py migrate
```
Собрать статику
```
sudo docker compose exec backend python manage.py collectstatic
```
Создать суперпользователя
```
sudo docker compose exec backend python manage.py createsuperuser
```
Наполнить базу данных
```
sudo docker compose exec backend python manage.py load_csv
```
## Примеры запросов к API
Получить список игредиентов
```
GET api/ingredients/
[
{
"id": 0,
"name": "Капуста",
"measurement_unit": "кг"
}
]
```
Создать рецепт
```
POST api/recipes/
Request:
{
"ingredients": [
{
"id": 1123,
"amount": 10
}
],
"tags": [
1,
2
],
"image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
"name": "string",
"text": "string",
"cooking_time": 1
}
Response:
{
"id": 0,
"tags": [
{}
],
"author": {
"email": "user@example.com",
"id": 0,
"username": "string",
"first_name": "Вася",
"last_name": "Пупкин",
"is_subscribed": false
},
"ingredients": [
{}
],
"is_favorited": true,
"is_in_shopping_cart": true,
"name": "string",
"image": "http://foodgram.example.org/media/recipes/images/image.jpeg",
"text": "string",
"cooking_time": 1
```
Просмотреть подписки
```
GET api/users/subscriptions/
{
"count": 123,
"next": "http://foodgram.example.org/api/users/subscriptions/?page=4",
"previous": "http://foodgram.example.org/api/users/subscriptions/?page=2",
"results": [
{
"email": "user@example.com",
"id": 0,
"username": "string",
"first_name": "Вася",
"last_name": "Пупкин",
"is_subscribed": true,
"recipes": [],
"recipes_count": 0
}
]
}
```
Больше примеров запросов доступно в документации.
## Стек технологий
+ Python 3.9
+ Django 3.2
+ Django REST framework 3.12.4
+ Nginx
+ Docker
+ Postgres
## Автор
```
Александр Чупахин
```

Email:

```
fisherr1@yandex.ru
```
