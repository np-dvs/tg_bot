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
    values = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for value in values:
        if value:
            return True
        else:
            logging.critical('Отсутствует токен')
            raise ValueError


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

# Павел, помогите, пожалуйста - 
# если я пишу конструкцию try-except такого плана
# я просто искусственно создаю TypeError, который
# попадёт в блок except
    # try:
    #     homework = response['homeworks']
    #     list = response['homeworks'][0]
    #     data = response['homeworks']
    # except TypeError as type:
    #     logging.error(f'Неверный тип данных - {type}')
    # except KeyError as key:
    #     logging.error(f'Не найден ключ {key}')
    # return data

    if not isinstance(response, dict):
        logging.error(f'Неверный тип данных.'
                      f'Был получен {type(response)}.'
                      f'Ожидался - {dict}')
        raise TypeError
    if 'homeworks' not in response:
        logging.error('Ключ "homeworks" отсутствует в словаре')
        raise KeyError
    if not isinstance(response.get('homeworks'), list):
        logging.error(f'Неверный тип данных.'
                      f'Был получен {type(response.get("homeworks"))}.'
                      f'Ожидался - {list}')
        raise TypeError
    return response['homeworks']


def parse_status(homework):
    """Проверяет статус домашней работы."""
    # if type(homework) is not dict:
    #     raise KeyError
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        verdict = HOMEWORK_VERDICTS[homework_status]
    except KeyError as key:
        logging.error(f'Ключ {key} не найден в словаре')
        raise KeyError
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
    check_tokens()
    while True:
        try:
            response = get_api_answer(timestamp - 20 * 24 * 60 * 60)
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

        time.sleep(600)


if __name__ == '__main__':
    main()
