from http import HTTPStatus


class ResponseError(Exception):
    def __init__(self, response):
        message = (
            f'Ошибка! Неверный код ответа'
            f'Ожидаемый код ответа - {HTTPStatus.OK}'
            f'Полученный код ответа - {response.status_code}'
            f'Адрес запроса: {response.url}.'
        )
        super().__init__(message)


class RequestExcept(Exception):
    def __init__(self, response):
        message = (f'При обработке запроса {response}'
                   f'Возникло исключение.')
        super().__init__(message)
