'''АВТОМАТИЗИРОВАННЫЙ ТЕСТЕР API СИСТЕМЫ "Предбиллинг" - ПОЛНЫЙ КЕЙС

Описание:
------------
Скрипт для создания, монтажа приборов учета, создания и удаления точек учета,
демонтажа приборов учета (теплосчетчик и водомер) через API

Последовательность действий для каждого типа прибора:
------------
1. Авторизация в системе
2. Создание ПУ с уникальным серийным номером
3. Монтаж ПУ на объект
4. Создание точки учета (ТУ) с этим ПУ
5. Получение ID созданной ТУ через виджет
6. Удаление ТУ
7. Демонтаж ПУ с объекта
8. Проверка результатов

Особенности:
------------
- Генерация уникальных 7-значных серийных номеров
- Автоматическое использование ID созданных ПУ для монтажа и демонтажа
- Получение ID точки учета через запрос к виджету после создания
- Установка текущей даты для всех операций
- type_operation: "CREATE" для монтажа
- event_code: 12 для монтажа
- Формирование objectName из серийного номера и модели
- Сохранение токена для последующих запросов
- Детальное логирование каждого шага
- Пауза 0.5 секунды между операциями
'''

import requests
import time
import random
import json
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime


class MeteringDeviceCase:
    def __init__(self, base_url: str = "http://10.5.121.74"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None

        # Константы для создания приборов учета
        self.BALANCE_CONSUMER_ID = "e429b940-d35a-4b75-8602-c2b2922e0200"
        self.CONTROLLER_ID = "c522508d-a837-4349-baab-08cf791b82e9"
        self.MODEL_ID = "4931c4ad-4f5b-405c-992d-f7163b1b6535"
        self.MODEL_NAME = "420PC"

        # ID объекта для монтажа/демонтажа
        self.ACCOUNTING_OBJECT_ID = "c789807c-c1d8-415b-8f52-d416d59091e8"

        # FillingStatus ID из примера
        self.FILLING_STATUS_ID = "d9d9a16a-3186-4921-a6f1-6e0817487804"

        # SystemEvent IDs из примера
        self.SYSTEM_EVENT_FINISH_ID = "e209f402-e4ac-4f25-8afe-33194f933971"
        self.SYSTEM_EVENT_ERROR_ID = "259694c1-8912-4f2b-9192-6ea3a1049672"

        # MeasureUnit ID для ТУ
        self.MEASURE_UNIT_ID = "2a31d2f4-ae06-437c-a807-cf46320ef454"

        # Статусы точек учета для поиска
        self.POINT_STATUSES = [1, 2, 3, 4, 6, 7, 8]

        # Типы приборов и соответствующие коды для ТУ
        self.DEVICE_TYPES = {
            "heat": {
                "constructType": 1,
                "constructTypeName": "Теплосчетчик",
                "kindMd": "1",
                "pointTypeCode": "04",  # Код для ТУ теплосчетчика
                "m1": 12,  # Для теплосчетчика используем m1
                "dateMeteringInitial": "2026-02-28T21:00:00.000Z"
            },
            "water": {
                "constructType": 2,
                "constructTypeName": "Водомер",
                "kindMd": "1",
                "pointTypeCode": "05",  # Код для ТУ водомера
                "startIv": 12,  # Для водомера используем startIv
                "nameSap": "-",  # Для водомера добавляем nameSap
                "dateMeteringInitial": "2025-06-30T21:00:00.000Z"
            }
        }

        # Базовый набор dataRoles
        self.DATA_ROLES = [
            "ADMIN", "COMMERCIAL_DIVISION", "COMMERCIAL_MANAGMENT", "DATA_ALL_OBJECTS",
            "DATA_ENTERPRISE_0", "DATA_ENTERPRISE_1", "DATA_ENTERPRISE_10", "DATA_ENTERPRISE_11",
            "DATA_ENTERPRISE_12", "DATA_ENTERPRISE_13", "DATA_ENTERPRISE_14", "DATA_ENTERPRISE_1_NPS",
            "DATA_ENTERPRISE_2", "DATA_ENTERPRISE_3", "DATA_ENTERPRISE_4", "DATA_ENTERPRISE_5",
            "DATA_ENTERPRISE_6", "DATA_ENTERPRISE_7", "DATA_ENTERPRISE_8", "DATA_ENTERPRISE_9",
            "DATA_MO", "DATA_NAO", "DATA_SALES_DEP_1", "DATA_SALES_DEP_10", "DATA_SALES_DEP_11",
            "DATA_SALES_DEP_2", "DATA_SALES_DEP_3", "DATA_SALES_DEP_4", "DATA_SALES_DEP_5",
            "DATA_SALES_DEP_6", "DATA_SALES_DEP_7", "DATA_SALES_DEP_8", "DATA_SALES_DEP_9",
            "DATA_SAO", "DATA_SVAO", "DATA_SZAO", "DATA_TAO", "DATA_TSAO", "DATA_UAO",
            "DATA_UVAO", "DATA_UZAO", "DATA_VAO", "DATA_ZAO", "DATA_ZELAO", "DATA_ZONE_10",
            "DATA_ZONE_111", "DATA_ZONE_12", "DATA_ZONE_14", "INTEGRATIONS", "PASSPORT",
            "ROLE", "ROLE_ALL_OBJECTS", "ROLE-TEST", "ROLE-TEST2", "TECHNOLOGICAL_DIVISION",
            "TECHNOLOGICAL_MANAGMENT", "TEST05122024", "WEATHER"
        ]

        # Результаты для каждого типа прибора
        self.results = {
            "heat": {
                "device_id": None,
                "serial_number": None,
                "point_id": None,
                "create": False,
                "mount": False,
                "point_create": False,
                "point_get": False,
                "point_delete": False,
                "dismantle": False
            },
            "water": {
                "device_id": None,
                "serial_number": None,
                "point_id": None,
                "create": False,
                "mount": False,
                "point_create": False,
                "point_get": False,
                "point_delete": False,
                "dismantle": False
            }
        }

    def get_current_datetime(self) -> str:
        """Возвращает текущую дату и время в формате ISO 8601"""
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    def generate_serial_number(self) -> str:
        """Генерация уникального 7-значного серийного номера"""
        serial = random.randint(1000000, 9999999)
        return str(serial)

    def get_object_name(self, serial_number: str) -> str:
        """Формирует objectName для демонтажа в формате 'серийный_номер (модель)'"""
        return f"{serial_number} ({self.MODEL_NAME})"

    def authenticate(self) -> bool:
        """Авторизация в системе"""
        print("\n" + "=" * 60)
        print("ЭТАП 1: АВТОРИЗАЦИЯ")
        print("=" * 60)

        url = f"{self.base_url}/api/auth/token"
        data = {
            "grant_type": "password",
            "username": "predbill",
            "password": "predbill"
        }

        try:
            start_time = time.time()
            response = self.session.post(url, data=data, timeout=(15, 30))
            response_time = time.time() - start_time

            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get('token')
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                print(f"АВТОРИЗАЦИЯ УСПЕШНА (200) [{response_time:.2f} сек]")
                return True
            else:
                print(f"ОШИБКА АВТОРИЗАЦИИ: статус {response.status_code} [{response_time:.2f} сек]")
                return False

        except Exception as e:
            print(f"ОШИБКА: {str(e)}")
            return False

    def create_device(self, device_type: str) -> Tuple[bool, Optional[str], Optional[str], float]:
        """
        Создание прибора учета
        device_type: "heat" или "water"
        Возвращает: (успех, ID устройства, серийный номер, время выполнения)
        """
        type_info = self.DEVICE_TYPES[device_type]
        type_name = type_info["constructTypeName"]

        print("\n" + "=" * 60)
        print(f"ЭТАП: СОЗДАНИЕ {type_name}")
        print("=" * 60)

        # Генерируем уникальный серийный номер
        serial_number = self.generate_serial_number()
        print(f"Генерируем серийный номер: {serial_number}")

        url = f"{self.base_url}/api/bear/script/sync/addMeteringDeviceFromFront"

        # Payload для создания ПУ
        payload = {
            "constructType": type_info["constructType"],
            "kindMd": type_info["kindMd"],
            "modelId": self.MODEL_ID,
            "balanceConsumerId": self.BALANCE_CONSUMER_ID,
            "controllerId": self.CONTROLLER_ID,
            "dataRoles": self.DATA_ROLES,
            "podp": [],
            "serialNumber": serial_number,
            "signMvk": False,
            "signPodp": False,
            "signSaldo": None,
            "signVirtual": False,
            "systemEvent": {
                "finish": {
                    "id": self.SYSTEM_EVENT_FINISH_ID,
                    "dataTemplate": {
                        "serialNumber": "serialNumber"
                    }
                },
                "error": {
                    "id": self.SYSTEM_EVENT_ERROR_ID,
                    "dataTemplate": {
                        "serialNumber": "serialNumber"
                    }
                }
            }
        }

        try:
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=(15, 30))
            response_time = time.time() - start_time

            if response.status_code == 200:
                response_data = response.json()
                device_id = response_data.get('id')

                if device_id:
                    print(f"ПРИБОР СОЗДАН УСПЕШНО (200) [{response_time:.2f} сек]")
                    print(f"  ID прибора: {device_id}")
                    print(f"  Серийный номер: {serial_number}")

                    # Сохраняем результаты
                    self.results[device_type]["device_id"] = device_id
                    self.results[device_type]["serial_number"] = serial_number
                    self.results[device_type]["create"] = True

                    return True, device_id, serial_number, response_time
                else:
                    print(f"ПРИБОР СОЗДАН, НО ID НЕ ПОЛУЧЕН (200) [{response_time:.2f} сек]")
                    return False, None, serial_number, response_time
            else:
                print(f"ОШИБКА СОЗДАНИЯ ПРИБОРА: статус {response.status_code} [{response_time:.2f} сек]")
                print(f"  Тело ответа: {response.text[:200]}")
                return False, None, serial_number, response_time

        except Exception as e:
            print(f"ОШИБКА: {str(e)}")
            return False, None, serial_number, 0

    def mount_device(self, device_type: str, device_id: str, serial_number: str) -> Tuple[bool, float]:
        """
        Монтаж созданного прибора учета на объект
        device_type: "heat" или "water"
        Возвращает: (успех, время выполнения)
        """
        type_info = self.DEVICE_TYPES[device_type]
        type_name = type_info["constructTypeName"]

        print("\n" + "=" * 60)
        print(f"ЭТАП: МОНТАЖ {type_name}")
        print("=" * 60)

        current_datetime = self.get_current_datetime()
        print(f"Дата монтажа: {current_datetime}")
        print(f"Объект для монтажа: {self.ACCOUNTING_OBJECT_ID}")
        print(f"ID прибора: {device_id}")
        print(f"Серийный номер: {serial_number}")

        url = f"{self.base_url}/api/bear/script/sync/addMeteringDeviceFromFront"

        # Полный payload для монтажа
        payload = {
            "id": device_id,
            "accObjectInfo": [{
                "codeFIAS": None,
                "btiUnom": None,
                "fullAddress": None
            }],
            "accountingObjectId": self.ACCOUNTING_OBJECT_ID,
            "addressId": None,
            "aoType": 2,
            "balanceConsumerId": self.BALANCE_CONSUMER_ID,
            "constructType": type_info["constructType"],
            "constructTypeCode": type_info["constructType"],
            "constructTypeName": type_name,
            "controllerId": self.CONTROLLER_ID,
            "controllerName": "Однопоточный",
            "dataForEquipmentHistory": {
                "accountingObjectId": self.ACCOUNTING_OBJECT_ID,
                "dateStart": current_datetime,
                "eventCode": 12,
                "typeOperation": "CREATE",
                "userDateOperation": current_datetime
            },
            "dataRoles": self.DATA_ROLES,
            "dateStart": current_datetime,
            "equipmentTypeName": "Прибор учета",
            "fillingStatus": {
                "id": self.FILLING_STATUS_ID,
                "title": "Не заполнен",
                "content": "В блоках карточки отсуствуют данные"
            },
            "fillingStatusId": self.FILLING_STATUS_ID,
            "heatPointNumber": None,
            "heatPointType": None,
            "interfaceNumber": None,
            "interfaceType": None,
            "kindMd": "3",
            "lastVerificationDate": None,
            "manufacturerId": None,
            "modelId": self.MODEL_ID,
            "modelName": self.MODEL_NAME,
            "modelPodpId": None,
            "networkNumber": None,
            "networkProtocol": None,
            "nextVerificationDate": None,
            "note": None,
            "numberGis": None,
            "numberGisGvs": None,
            "numberGisTe": None,
            "numberVPU": None,
            "periodicityCode": None,
            "podp": [],
            "pollingPeriod": 60,
            "remoteRelease": None,
            "serialNumber": serial_number,
            "serialNumberPodp": None,
            "signMvk": False,
            "signPodp": False,
            "signSaldo": None,
            "signVirtual": False,
            "speedCode": None,
            "systemEvent": {
                "finish": {
                    "id": self.SYSTEM_EVENT_FINISH_ID,
                    "dataTemplate": {
                        "serialNumber": "serialNumber"
                    }
                },
                "error": {
                    "id": self.SYSTEM_EVENT_ERROR_ID,
                    "dataTemplate": {
                        "serialNumber": "serialNumber"
                    }
                }
            },
            "tcpPort": None,
            "transmissionDeviceId": None
        }

        try:
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=(15, 30))
            response_time = time.time() - start_time

            if response.status_code == 200:
                print(f"МОНТАЖ ВЫПОЛНЕН УСПЕШНО (200) [{response_time:.2f} сек]")
                print(f"  Прибор {serial_number} смонтирован на объект {self.ACCOUNTING_OBJECT_ID}")
                self.results[device_type]["mount"] = True
                return True, response_time
            else:
                print(f"ОШИБКА МОНТАЖА: статус {response.status_code} [{response_time:.2f} сек]")
                print(f"  Тело ответа: {response.text[:200]}")
                return False, response_time

        except Exception as e:
            print(f"ОШИБКА: {str(e)}")
            return False, 0

    def get_point_id_by_device(self, device_type: str, device_id: str) -> Tuple[bool, Optional[str], float]:
        """
        Получение ID точки учета по ID прибора через виджет
        device_type: "heat" или "water"
        Возвращает: (успех, ID точки учета, время выполнения)
        """
        type_info = self.DEVICE_TYPES[device_type]
        type_name = type_info["constructTypeName"]

        print("\n" + "=" * 60)
        print(f"ЭТАП: ПОИСК ID ТОЧКИ УЧЕТА ДЛЯ {type_name}")
        print("=" * 60)

        url = f"{self.base_url}/api/bear/script/sync/flat/meteringPointsWidgetByAccObjectPredBill?page=0&size=50"

        payload = {
            "accountingObjectId": self.ACCOUNTING_OBJECT_ID,
            "dataRoles": self.DATA_ROLES,
            "status": self.POINT_STATUSES
        }

        print(f"Поиск точки учета для прибора: {device_id}")

        try:
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=(15, 30))
            response_time = time.time() - start_time

            if response.status_code == 200:
                points = response.json()
                print(f"Получено точек учета: {len(points)}")

                # Ищем точку с нашим ID прибора
                for point in points:
                    if point.get('meteringDeviceId') == device_id:
                        point_id = point.get('id')
                        if point_id:
                            print(f"НАЙДЕНА ТОЧКА УЧЕТА:")
                            print(f"  ID точки: {point_id}")
                            print(f"  Тип: {point.get('typeName')}")
                            print(f"  Статус: {point.get('statusName')}")

                            self.results[device_type]["point_id"] = point_id
                            self.results[device_type]["point_get"] = True

                            return True, point_id, response_time

                print(f"Точка учета для прибора {device_id} не найдена")
                return False, None, response_time
            else:
                print(f"ОШИБКА ПОЛУЧЕНИЯ СПИСКА ТОЧЕК: статус {response.status_code} [{response_time:.2f} сек]")
                print(f"  Тело ответа: {response.text[:200]}")
                return False, None, response_time

        except Exception as e:
            print(f"ОШИБКА: {str(e)}")
            return False, None, 0

    def create_point(self, device_type: str, device_id: str) -> Tuple[bool, float]:
        """
        Создание точки учета для прибора
        device_type: "heat" или "water"
        Возвращает: (успех, время выполнения)
        """
        type_info = self.DEVICE_TYPES[device_type]
        type_name = type_info["constructTypeName"]

        print("\n" + "=" * 60)
        print(f"ЭТАП: СОЗДАНИЕ ТОЧКИ УЧЕТА ДЛЯ {type_name}")
        print("=" * 60)

        url = f"{self.base_url}/api/bear/script/sync/addManualPointPredBill"

        # Базовый payload для ТУ
        payload = {
            "meteringDeviceId": device_id,
            "accountingObjectId": self.ACCOUNTING_OBJECT_ID,
            "typeCode": type_info["pointTypeCode"],
            "branchPipe": False,
            "channel": None,
            "dataRoles": self.DATA_ROLES,
            "date": None,
            "dateMeteringInitial": type_info["dateMeteringInitial"],
            "descPressureMeter": None,
            "descTempSensor": None,
            "measureUnitId": self.MEASURE_UNIT_ID,
            "premisesId": None,
            "serviceSubjectAgreements": [],
            "standPlaceId": None,
            "typeAction": "add",
            "userId": 483
        }

        # Добавляем специфичные для типа поля
        if device_type == "heat":
            payload["m1"] = type_info["m1"]
        else:  # water
            payload["startIv"] = type_info["startIv"]
            payload["nameSap"] = type_info["nameSap"]

        print(f"ID прибора: {device_id}")
        print(f"Тип точки учета: {type_info['pointTypeCode']}")

        try:
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=(15, 30))
            response_time = time.time() - start_time

            if response.status_code == 200:
                print(f"ТОЧКА УЧЕТА СОЗДАНА УСПЕШНО (200) [{response_time:.2f} сек]")
                print(f"  ID точки учета будет получен отдельным запросом")
                self.results[device_type]["point_create"] = True
                return True, response_time
            else:
                print(f"ОШИБКА СОЗДАНИЯ ТОЧКИ УЧЕТА: статус {response.status_code} [{response_time:.2f} сек]")
                print(f"  Тело ответа: {response.text[:200]}")
                return False, response_time

        except Exception as e:
            print(f"ОШИБКА: {str(e)}")
            return False, 0

    def delete_point(self, device_type: str, point_id: str) -> Tuple[bool, float]:
        """
        Удаление точки учета
        device_type: "heat" или "water"
        Возвращает: (успех, время выполнения)
        """
        type_info = self.DEVICE_TYPES[device_type]
        type_name = type_info["constructTypeName"]

        print("\n" + "=" * 60)
        print(f"ЭТАП: УДАЛЕНИЕ ТОЧКИ УЧЕТА ДЛЯ {type_name}")
        print("=" * 60)

        url = f"{self.base_url}/api/bear/script/sync/deleteMeteringPointInPredbillAndPsd"

        payload = {
            "meteringPointId": point_id,
            "commercialNodeId": None,
            "dataRoles": self.DATA_ROLES,
            "historyMpExplId": None
        }

        print(f"ID точки учета для удаления: {point_id}")

        try:
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=(15, 30))
            response_time = time.time() - start_time

            if response.status_code == 200:
                print(f"ТОЧКА УЧЕТА УДАЛЕНА УСПЕШНО (200) [{response_time:.2f} сек]")
                self.results[device_type]["point_delete"] = True
                return True, response_time
            else:
                print(f"ОШИБКА УДАЛЕНИЯ ТОЧКИ УЧЕТА: статус {response.status_code} [{response_time:.2f} сек]")
                print(f"  Тело ответа: {response.text[:200]}")
                return False, response_time

        except Exception as e:
            print(f"ОШИБКА: {str(e)}")
            return False, 0

    def dismantle_device(self, device_type: str, device_id: str, serial_number: str) -> Tuple[bool, float]:
        """
        Демонтаж прибора учета с объекта
        device_type: "heat" или "water"
        Возвращает: (успех, время выполнения)
        """
        type_info = self.DEVICE_TYPES[device_type]
        type_name = type_info["constructTypeName"]

        print("\n" + "=" * 60)
        print(f"ЭТАП: ДЕМОНТАЖ {type_name}")
        print("=" * 60)

        current_datetime = self.get_current_datetime()
        object_name = self.get_object_name(serial_number)

        print(f"Дата демонтажа: {current_datetime}")
        print(f"Объект для демонтажа: {self.ACCOUNTING_OBJECT_ID}")
        print(f"ID прибора: {device_id}")
        print(f"Серийный номер: {serial_number}")
        print(f"Object name: {object_name}")

        url = f"{self.base_url}/api/bear/script/sync/dismantlingMeteringDevice"

        # Payload для демонтажа
        payload = {
            "accountingObjectId": self.ACCOUNTING_OBJECT_ID,
            "dataRoles": self.DATA_ROLES,
            "meteringDeviceId": device_id,
            "objectName": object_name,
            "userDateOperation": current_datetime
        }

        try:
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=(15, 30))
            response_time = time.time() - start_time

            if response.status_code == 200:
                print(f"ДЕМОНТАЖ ВЫПОЛНЕН УСПЕШНО (200) [{response_time:.2f} сек]")
                print(f"  Прибор {serial_number} демонтирован с объекта {self.ACCOUNTING_OBJECT_ID}")

                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and response_data.get('id'):
                        print(f"  ID записи демонтажа: {response_data.get('id')}")
                except:
                    pass

                self.results[device_type]["dismantle"] = True
                return True, response_time
            else:
                print(f"ОШИБКА ДЕМОНТАЖА: статус {response.status_code} [{response_time:.2f} сек]")
                print(f"  Тело ответа: {response.text}")
                return False, response_time

        except Exception as e:
            print(f"ОШИБКА: {str(e)}")
            return False, 0

    def run_device_cycle(self, device_type: str):
        """Запуск полного цикла для одного типа прибора"""
        type_info = self.DEVICE_TYPES[device_type]
        type_name = type_info["constructTypeName"]

        print(f"\n{'=' * 70}")
        print(f"ЗАПУСК ПОЛНОГО ЦИКЛА ДЛЯ: {type_name}")
        print(f"{'=' * 70}")

        # Шаг 1: Создание ПУ
        create_success, device_id, serial_number, create_time = self.create_device(device_type)
        if not create_success or not device_id:
            print(f"ОШИБКА: Не удалось создать {type_name}. Цикл прерван.")
            return

        time.sleep(0.5)

        # Шаг 2: Монтаж ПУ
        mount_success, mount_time = self.mount_device(device_type, device_id, serial_number)
        if not mount_success:
            print(f"ОШИБКА: Не удалось смонтировать {type_name}. Цикл прерван.")
            return

        time.sleep(0.5)

        # Шаг 3: Создание ТУ
        point_create_success, point_create_time = self.create_point(device_type, device_id)
        if not point_create_success:
            print(f"ОШИБКА: Не удалось создать точку учета для {type_name}. Цикл прерван.")
            return

        time.sleep(0.5)

        # Шаг 4: Получение ID ТУ через виджет
        point_get_success, point_id, point_get_time = self.get_point_id_by_device(device_type, device_id)
        if not point_get_success or not point_id:
            print(f"ОШИБКА: Не удалось получить ID точки учета для {type_name}. Цикл прерван.")
            return

        time.sleep(0.5)

        # Шаг 5: Удаление ТУ
        delete_point_success, delete_point_time = self.delete_point(device_type, point_id)

        time.sleep(0.5)

        # Шаг 6: Демонтаж ПУ
        dismantle_success, dismantle_time = self.dismantle_device(device_type, device_id, serial_number)

        # Промежуточный отчет по типу
        print(f"\n{'-' * 70}")
        print(f"РЕЗУЛЬТАТЫ ЦИКЛА ДЛЯ {type_name}:")
        print(f"  Создание ПУ: {'УСПЕШНО' if create_success else 'ОШИБКА'}")
        print(f"  Монтаж ПУ: {'УСПЕШНО' if mount_success else 'ОШИБКА'}")
        print(f"  Создание ТУ: {'УСПЕШНО' if point_create_success else 'ОШИБКА'}")
        print(f"  Получение ID ТУ: {'УСПЕШНО' if point_get_success else 'ОШИБКА'}")
        print(f"  Удаление ТУ: {'УСПЕШНО' if delete_point_success else 'ОШИБКА'}")
        print(f"  Демонтаж ПУ: {'УСПЕШНО' if dismantle_success else 'ОШИБКА'}")
        print(f"  Серийный номер: {serial_number}")
        print(f"  ID прибора: {device_id}")
        print(f"  ID точки учета: {point_id if point_id else 'не получен'}")
        print(f"{'-' * 70}")

    def run_full_case(self):
        """Запуск полного кейса для всех типов приборов"""
        print("\n" + "=" * 80)
        print("ЗАПУСК ПОЛНОГО КЕЙСА: ТЕПЛОСЧЕТЧИК И ВОДОМЕР С ТОЧКАМИ УЧЕТА")
        print("=" * 80)
        print(f"Время старта: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Объект учета: {self.ACCOUNTING_OBJECT_ID}")

        start_time = time.time()

        # Шаг 1: Авторизация
        if not self.authenticate():
            print("КЕЙС ПРЕРВАН: Ошибка авторизации")
            return

        time.sleep(0.5)

        # Шаг 2: Цикл для теплосчетчика
        self.run_device_cycle("heat")

        time.sleep(0.5)

        # Шаг 3: Цикл для водомера
        self.run_device_cycle("water")

        # Финальный отчет
        print("\n" + "=" * 80)
        print("ФИНАЛЬНЫЙ ОТЧЕТ")
        print("=" * 80)

        total_time = time.time() - start_time

        print(f"Общее время выполнения: {total_time:.2f} сек")
        print(f"\nРЕЗУЛЬТАТЫ ПО ТИПАМ ПРИБОРОВ:")

        for device_type, type_info in self.DEVICE_TYPES.items():
            type_name = type_info["constructTypeName"]
            res = self.results[device_type]

            print(f"\n{type_name}:")
            print(f"  Серийный номер: {res['serial_number'] or 'не создан'}")
            print(f"  ID прибора: {res['device_id'] or 'не создан'}")
            print(f"  ID точки учета: {res['point_id'] or 'не получен'}")
            print(f"  Создание ПУ: {'✓' if res['create'] else '✗'}")
            print(f"  Монтаж ПУ: {'✓' if res['mount'] else '✗'}")
            print(f"  Создание ТУ: {'✓' if res['point_create'] else '✗'}")
            print(f"  Получение ID ТУ: {'✓' if res['point_get'] else '✗'}")
            print(f"  Удаление ТУ: {'✓' if res['point_delete'] else '✗'}")
            print(f"  Демонтаж ПУ: {'✓' if res['dismantle'] else '✗'}")

        # Общий итог
        heat_ok = all([
            self.results["heat"]["create"],
            self.results["heat"]["mount"],
            self.results["heat"]["point_create"],
            self.results["heat"]["point_get"],
            self.results["heat"]["point_delete"],
            self.results["heat"]["dismantle"]
        ])

        water_ok = all([
            self.results["water"]["create"],
            self.results["water"]["mount"],
            self.results["water"]["point_create"],
            self.results["water"]["point_get"],
            self.results["water"]["point_delete"],
            self.results["water"]["dismantle"]
        ])

        print(f"\nИТОГ:")
        if heat_ok and water_ok:
            print("  ПОЛНЫЙ ЦИКЛ ВЫПОЛНЕН УСПЕШНО ДЛЯ ОБОИХ ТИПОВ ПРИБОРОВ")
            print("  Все приборы созданы, смонтированы, созданы и удалены точки учета, приборы демонтированы")
        elif heat_ok:
            print("  ТЕПЛОСЧЕТЧИК: полный цикл успешен")
            print("  ВОДОМЕР: есть ошибки в выполнении цикла")
        elif water_ok:
            print("  ВОДОМЕР: полный цикл успешен")
            print("  ТЕПЛОСЧЕТЧИК: есть ошибки в выполнении цикла")
        else:
            print("  ЕСТЬ ОШИБКИ В ВЫПОЛНЕНИИ ЦИКЛОВ")

        print("=" * 80)


if __name__ == "__main__":
    # Создаем экземпляр класса и запускаем полный кейс
    case = MeteringDeviceCase()
    case.run_full_case()