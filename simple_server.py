from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
import json
from datetime import date, timedelta, datetime
from bitrix24 import Bitrix24, BitrixError
import configparser


config = configparser.ConfigParser()
config.read('config.cfg')  # достаем вебхук для вызова rest api
bx24 = Bitrix24(config.get('BITRIX_API', 'CALL_URL'))  # подключаемся к битриксу;

def get_contact(phone):
    """ Возвращает список контактов с указанным номерм телефона"""
    return (bx24.callMethod('crm.contact.list', filter={"PHONE": phone}, select=["ID", "NAME"]))

def make_deal(json_data):
    """ Обрабатываем сделку по алгоритму, в первом случае добавляем сделку контакту,
    во вотором создаем новый контакт и сделку"""
    if len(get_contact(json_data['client']['phone'][1:])) > 0:
        deal_id = bx24.callMethod('crm.deal.list', filter={"UF_CRM_DELIVERY_CODE": json_data['delivery_code'][1:]}, select=["ID"])
        if len(deal_id) != 0:
            update_status = False
            deal = bx24.callMethod('crm.deal.get', id=deal_id[0]['ID'])
            if deal["UF_CRM_DELIVERY_ADRESS"] != json_data['delivery_adress']:
                deal["UF_CRM_DELIVERY_ADRESS"] = json_data['delivery_adress']
                update_status = True
            if deal["UF_CRM_DELIVERY_DATE"] != (datetime.strptime(json_data['delivery_date'], "%Y-%m-%d:%H:%M")):
                deal["UF_CRM_DELIVERY_DATE"] = (datetime.strptime(json_data['delivery_date'], "%Y-%m-%d:%H:%M"))
                update_status = True
            if deal["UF_CRM_GOODS"] != ' '.join(json_data['products']):
                deal["UF_CRM_GOODS"] = ' '.join(json_data['products'])
                update_status = True
            if update_status is True:
                bx24.callMethod('crm.deal.update', id=deal_id[0]['ID'], fields={
                    "UF_CRM_DELIVERY_ADRESS": deal["UF_CRM_DELIVERY_ADRESS"],
                    "UF_CRM_DELIVERY_DATE": deal["UF_CRM_DELIVERY_DATE"],
                    "UF_CRM_GOODS": deal["UF_CRM_GOODS"],
                })
    else:
        bx24.callMethod('crm.contact.add', fields={
            "NAME": json_data['client']['name'],
            "LAST_NAME": json_data['client']['surname'],
            "TYPE_ID": "CLIENT",
            "SOURCE_ID": "SELF",
            "PHONE": [{"VALUE": json_data['client']['phone'][1:], "VALUE_TYPE": "WORK"}]
        })
        contact = get_contact(json_data['client']['phone'][1:])
        contact_id = contact[0]['ID']
        bx24.callMethod('crm.deal.add', fields={
            "TITLE": "Плановая продажа",
            "TYPE_ID": "GOODS",
            "STAGE_ID": "NEW",
            "CONTACT_ID": contact_id,
            "UF_CRM_DELIVERY_ADRESS": json_data['delivery_adress'],
            "UF_CRM_DELIVERY_DATE": (datetime.strptime(json_data['delivery_date'], "%Y-%m-%d:%H:%M")),
            "UF_CRM_DELIVERY_CODE": json_data['delivery_code'][1:],
            "UF_CRM_GOODS": ' '.join(json_data['products'])
        })

def get_user_fields():
    """ Возвращает список кастомных полей созданных пользователем"""
    return bx24.callMethod('crm.deal.userfield.list')

def make_user_fields():
    """ Создает необходимые поля"""
    bx24.callMethod('crm.deal.userfield.add', fields={
        "FIELD_NAME": "DELIVERY_ADRESS",
        "EDIT_FORM_LABEL": "Адрес доставки",
        "LIST_COLUMN_LABEL": "Адрес доставки",
        "USER_TYPE_ID": "string",
        "XML_ID": "DELIVERY_ADRESS",
    })
    bx24.callMethod('crm.deal.userfield.add', fields={
        "FIELD_NAME": "DELIVERY_DATE",
        "EDIT_FORM_LABEL": "Дата доставки",
        "LIST_COLUMN_LABEL": "Дата доставки",
        "USER_TYPE_ID": "datetime",
        "XML_ID": "DELIVERY_DATE",
    })
    bx24.callMethod('crm.deal.userfield.add', fields={
        "FIELD_NAME": "DELIVERY_CODE",
        "EDIT_FORM_LABEL": "Код доставки",
        "LIST_COLUMN_LABEL": "Код доставки",
        "USER_TYPE_ID": "string",
        "XML_ID": "DELIVERY_CODE",
    })
    bx24.callMethod('crm.deal.userfield.add', fields={
        "FIELD_NAME": "GOODS",
        "EDIT_FORM_LABEL": "Товары",
        "LIST_COLUMN_LABEL": "Товары",
        "USER_TYPE_ID": "string",
        "XML_ID": "GOODS",
    })


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """ Отображаем текст на странице при GET-запросе"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Some Python app for Bitrix24')

    def do_POST(self):
        """ Возвращаем респонс, обрабатываем сделку в Б24"""
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        self.send_response(200)
        self.send_header('Content-type', 'json')
        self.end_headers()
        response = BytesIO()

        json_data = body.decode('utf8').replace("'", '"')
        print(json_data)
        print(type(json_data))
        json_data = json.loads(json_data)
        print(type(json_data))
        if len(get_user_fields()) == 0:
            make_user_fields()
        make_deal(json_data)
        response.write(b'Bitrix24 data is created\updated ')
        self.wfile.write(response.getvalue())



httpd = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
httpd.serve_forever()