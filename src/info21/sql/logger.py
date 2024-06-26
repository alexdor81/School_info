import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler


class LoggingMiddleware:
    """Класс логгера."""

    def __init__(self, get_response):
        # Создаем и настраиваем логгер
        self.get_response = get_response
        log_format = "%(asctime)s [%(levelname)s] %(message)s"
        self.logger = logging.getLogger("user_actions")
        self.logger.setLevel(logging.DEBUG)
        now = datetime.now().strftime("%d-%m-%y-%H-%M-%S")
        logs_dir = os.path.abspath(__file__).replace(
            os.path.basename(__file__), "../logs/"
        )
        if not os.path.exists("logs"):
            os.mkdir("logs")
        log_filename = f"{logs_dir}logs_{now}.log"
        file_handler = TimedRotatingFileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        self.logger.addHandler(file_handler)

    def __call__(self, request):
        # Логгирование действий пользователя с помощью методов info, error и
        # warning, в зависимости от статуса ответа на запрос
        request.logger = self.logger
        response = self.get_response(request)
        if response.status_code == 200:
            self.logger.info(
                "%s %s %s %s",
                request.method,
                request.path,
                response.status_code,
                request.META.get("REMOTE_ADDR"),
            )
        elif response.status_code >= 500:
            self.logger.error(
                "%s %s %s %s",
                request.method,
                request.path,
                response.status_code,
                request.META.get("REMOTE_ADDR"),
            )
        else:
            self.logger.warning(
                "%s %s %s %s",
                request.method,
                request.path,
                response.status_code,
                request.META.get("REMOTE_ADDR"),
            )
        return response
