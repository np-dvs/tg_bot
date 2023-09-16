from http import HTTPStatus
import requests

class ResponseError(Exception):
    def __init__(self, response):
        message = (
            f'Ошибка! Неверный код ответа'
            f'Ожидаемый код ответа - {HTTPStatus.OK}'
            f'Полученный код ответа - {response.status_code}'
            f'Адрес запроса: {response.url}.'
        )
        super().__init__(message)


class RequestExcept(requests.RequestException):
    def __init__(self, request):
        message = (f'При обработке запроса {request}'
                   f'Возникло исключение.')
        super().__init__(message)
