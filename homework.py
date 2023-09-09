import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
import telegram.ext
from dotenv import load_dotenv

from exceptions import HTTPRequestError

load_dotenv()


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
LAST_HW_DATE = 20 * 24 * 60 * 60
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """
    Проверяет доступность переменных окружения.
    Если отсутствует хотя бы одна переменная окружения
    продолжать работу бота нет смысла.
    """
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return True


def get_api_answer(timestamp):
    """
    Делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка
    """
    payload = {'from_date': timestamp}
    try:
        server_response = requests.get(ENDPOINT,
                                       headers=HEADERS,
                                       params=payload)
        if server_response.status_code != HTTPStatus.OK:
            logging.error(f'Код ответа {server_response.status_code}')
            raise HTTPRequestError
    except requests.RequestException:
        logging.error('Не удалось получить ответ API')
    return server_response.json()


def check_response(response):
    """
    Проверяет ответ - тип dict.
    Ключи - homeworks, current_date.
    Тип значения ключа homeworks - list.
    """
    if not isinstance(response, dict):
        raise TypeError(f'Неверный тип данных - {type(response)}.'
                        f'Ожидался - {dict}')
    if 'homeworks' not in response:
        raise KeyError('Ключ "homeworks" отсутствует в словаре')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError(f'Неверный тип данных -'
                        f'{type(response.get("homeworks"))}.'
                        f'Ожидался - {list}')
    return response['homeworks']


def parse_status(homework):
    """Проверяет статус домашней работы."""
    if not isinstance(homework, dict):
        raise TypeError(f'Неверный тип данных - {type(homework)}.'
                        f'Ожидаемый тип данных - {dict}.')
    keys = ['homework_name', 'status']
    for key in keys:
        if key not in homework:
            raise KeyError(f'Ключ {key} не найден в словаре.')
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise KeyError(f'Ключ {key} не найден в словаре')
    else:
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')
        verdict = HOMEWORK_VERDICTS.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Отправляет обновление домашки в чат."""
    try:
        logging.debug('Cообщение отправлено')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        logging.error('Не удалось отправить сообщение')


def main():
    """Основная логика работы бота."""
    """Проверка токенов"""
    last_status = []
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    if not check_tokens():
        logging.critical('Отсутствует переменная окружения.'
                         'Программа принудительно остановлена.')
        exit()
    while True:
        try:
            response = get_api_answer(timestamp - LAST_HW_DATE)
            homeworks = check_response(response)
            for homework in homeworks:
                message = parse_status(homework)
                if homework['status'] not in last_status:
                    last_status.append(homework['status'])
                    send_message(bot, message)
                else:
                    send_message(bot, 'Статус не обновлялся')
                    logging.debug('Статус не обновлялся')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
