# Это Foodgram: дипломный проект! разработан со следующим стеком техноголгий:

 - Django Rest Framework
 - PostgreSQL
 - GitHub Actions
 - Docker

## Проект предназначен для удобства обмена кулинарными рецептами и оптимизации составления списка покупок.

 - Для деплоя проекта требуется:
    - настроить для репозитория следующие секреты:
     - DOCKER_LOGIN
     - DOCKER PASSOWORD
     - HOST (IP сервера)
     - USER (Имя пальзователя на сервере)
     - SSH_KEY
     - SSH_PHASSPHRASE
    - запушить проет на ветку main.

 - Для корректной работы потребуется разместить в корневой директории файл **.env** со следующими переменными:
    - POSTGRES_DB=exemple_db_name
    - POSTGRES_USER=exemple_user
    - POSTGRES_PASSWORD=exemple_password
    - DB_HOST=db 
    - DB_PORT=5432
    - DEBUG_MODE=false
    - SECRET_KEY=exemple_secret_key
    - ALLOWED_HOSTS= ip.of.your.host, your-own-domain.exemple.ru, localhost

### В разработе учавствовали [Дубровин Павел](https://github.com/PavelDubrovin93), Александр Дурнев и [Андрей Дубинчик](https://github.com/evi1ghost). При вспомоществовании Яндекс.Практиум