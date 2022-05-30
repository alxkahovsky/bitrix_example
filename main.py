from datetime import date, timedelta, datetime
import holidays
from bitrix24 import Bitrix24, BitrixError
import configparser


holidays_ru = holidays.Russia(years=2022)
today = datetime.today().strftime('%Y-%m-%d')
# today = '2022-01-02'  # date string for development and testing
if holidays_ru.get(datetime.strptime(today, '%Y-%m-%d') + timedelta(days=3)) is None \
        or holidays_ru.get(datetime.strptime(today, '%Y-%m-%d')) is not None:
    print(today, "Создавать задачу не нужно")
else:
    config = configparser.ConfigParser()
    config.read('config.cfg')
    bx24 = Bitrix24(config.get('BITRIX_API', 'CALL_URL'))
    print('Внимание', datetime.strptime(today, '%Y-%m-%d') + timedelta(days=3),
          holidays_ru.get(datetime.strptime(today, '%Y-%m-%d') + timedelta(days=3)))
    try:
        bx24.callMethod('tasks.task.add', fields={
            'TITLE': holidays_ru.get(datetime.strptime(today, '%Y-%m-%d') + timedelta(days=3)) + ' будет через 3 дня',
            'RESPONSIBLE_ID': 1,
            'START_DATE_PLAN': today,
            'END_DATE_PLAN': today
            })
    except BitrixError as message:
        print(message)
