import logging

from auth_service import AuthService

logging.basicConfig(level=logging.INFO)


def main():
    """
    Главная функция приложения для демонстрации работы AuthService
    """
    auth_service = AuthService()

    username = "user1"
    password = "password123"

    # Регистрация пользователя
    token = auth_service.register(username, password)
    if token:
        logging.info(f"Пользователь успешно зарегистрирован. Токен: {token}")
    else:
        logging.info("Пользователь с таким именем уже существует.")

    # Аутентификация пользователя
    auth_token = auth_service.authenticate(username, password)
    if auth_token:
        logging.info(
            f"Пользователь успешно аутентифицирован. Обновленный токен: {auth_token}")
    else:
        logging.info(
            "Ошибка аутентификации: неверное имя пользователя или пароль")


if __name__ == "__main__":
    main()  # комментарий
