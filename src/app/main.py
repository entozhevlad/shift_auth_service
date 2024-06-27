import logging


def get_greetings() -> str:
    """Возвращает строку приветствия."""
    return 'Hello World!'


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.info(get_greetings())
