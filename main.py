import logging

from src.app.services.auth_service import AuthService

logging.basicConfig(level=logging.INFO)


def main():
    """Функция приложения для демонстрации работы AuthService."""
    auth_service = AuthService()

    username = 'user'
    test_pass = 'qwerty735'

    # Регистрация пользователя
    token = auth_service.register(username, test_pass)
    if token:
        logging.info(
            'Пользователь успешно зарегистрирован. Токен: {0}'.format(token),
        )
    else:
        logging.info('Пользователь с таким именем уже существует.')

    # Аутентификация пользователя
    auth_token = auth_service.authenticate(username, test_pass)
    if auth_token:
        logging.info(
            'Пользователь аутентифицирован. Токен: {0}'.format(auth_token),
        )
    else:
        logging.info(
            'Ошибка аутентификации: неверное имя пользователя или пароль',
        )


if __name__ == '__main__':
    main()
