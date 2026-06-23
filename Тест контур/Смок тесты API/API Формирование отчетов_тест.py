'''ТЕСТ API "ФОРМИРОВАНИЕ ОТЧЕТОВ"

Описание:
------------
Скрипт для тестирования формирования отчетов через RabbitMQ
Постепенное добавление новых отчетов

Текущая версия: 21 отчет
- Отчёт о проверке ведомостей (обобщенный)
- Отчёт о проверке ведомостей (детальный)
- Отчёт об обработке ведомостей за период
- Отчет по Приборам учета
- Отчет по Точкам учета
- Отчет о количестве строений с ПУ
- Отчет по приборам учета с просроченной поверкой
- Отчет по сверке ОДПУ с данными ГИС ЖКХ
- Отчет зафиксированных конфликтов данных между показаниями приборов учета и отключенными установками
- Анализ показаний ОДУУ за 3 периода
- Отчет по вводу показаний ПУ в разрезе муниципальных районов
- Отчет о снятии показаний по точкам учета
- Отчет по температуре наружного воздуха
- Отчет о замене приборов учета МВК
- Отчет по запитке
- Отчет о переданных ведомостях за период
- Отчет о передаче показаний в АС «Мосводоканал»
- Активные показания ПУ не идущие в расчёт
- Отчет о результатах передачи данных через ЕЛК для водомеров
- Отчет по Сим-картам
- Отчет по УСПД

Последовательность действий:
------------
1. Авторизация в системе
2. Для каждого отчета из конфигурации:
   - Выбираются случайные параметры (период и/или округ)
   - Отправка запроса на формирование отчета с retry-механизмом
   - Получение reportTaskId из ответа
   - Циклический опрос статуса отчета каждую секунду
   - Ожидание статуса READY (максимум 10 минут)
   - Фиксация результата и времени формирования
3. Генерация детального отчета по всем тестам
'''

import requests
import time
import json
import random
import traceback
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta


class ReportTester:
    def __init__(self, base_url: str = "http://10.5.121.80:4980"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.results = []

        # Максимальное время ожидания отчета (10 минут)
        self.MAX_WAIT_TIME = 600  # секунд
        self.POLL_INTERVAL = 1     # секунда
        self.PAUSE_BETWEEN_TESTS = 3  # пауза между отчетами 3 секунды
        self.SHORT_WAIT_TIME = 300  # 5 минут для статусов QUEUED/NOT_FOUND
        self.REQUEST_TIMEOUT = 45  # 45 секунд на подключение

        # Retry механизмы
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5  # секунд между попытками

        # Список административных округов (названия)
        self.AO_DISTRICT_NAMES = [
            "ВАО", "ЦАО", "ЗелАО", "ЮАО", "ЮЗАО", "СЗАО",
            "САО", "ТАО", "МО", "НАО", "СВАО", "ЗАО", "ЮВАО"
        ]

        # Список административных округов (коды)
        # Соответствие: ВАО=1, ЦАО=2, ЗелАО=3, ЮАО=4, ЮЗАО=5, СЗАО=6,
        # САО=7, ТАО=8, МО=9, НАО=10, СВАО=11, ЗАО=12, ЮВАО=13
        self.AO_DISTRICT_CODES = [str(i) for i in range(1, 14)]

        # Маппинг кодов округов в названия
        self.AO_CODE_TO_NAME = {
            "1": "ВАО", "2": "ЦАО", "3": "ЗелАО", "4": "ЮАО", "5": "ЮЗАО", "6": "СЗАО",
            "7": "САО", "8": "ТАО", "9": "МО", "10": "НАО", "11": "СВАО", "12": "ЗАО", "13": "ЮВАО"
        }

        # Форматы выгрузки для отчетов
        self.REPORT_FORMATS = ["addressable", "summary", "detailed"]

        # Конфигурация отчетов
        self.REPORTS = {
            # Отчеты по ведомостям (с периодом и названием округа)
            "report_checks_general": {
                "id": "5149b174-abc6-48c8-8c55-1ec8b6f888d6",
                "name": "Отчёт о проверке ведомостей (обобщенный)",
                "config": "01_report_checks",
                "group": "Ведомости",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": True,
                "district_field": "aoDistrictName",
                "district_type": "name",
                "active": True
            },
            "report_checks_detailed": {
                "id": "b0cbec9c-3e34-44c7-bc15-38d480deef78",
                "name": "Отчёт о проверке ведомостей (детальный)",
                "config": "02_report_checks",
                "group": "Ведомости",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": True,
                "district_field": "aoDistrictName",
                "district_type": "name",
                "active": True
            },
            "report_processing_period": {
                "id": "c0814c51-30bc-499d-b48a-7a2d7b6eed1e",
                "name": "Отчёт об обработке ведомостей за период",
                "config": "04_report_checks",
                "group": "Ведомости",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": True,
                "district_field": "aoDistrictName",
                "district_type": "name",
                "active": True
            },

            # Отчет по приборам учета (только округ, код)
            "report_metering_devices": {
                "id": "53b3e7ea-386a-4e28-8736-639e589556f6",
                "name": "Отчет по Приборам учета",
                "config": "meteringDevicesPredBill",
                "group": "Приборы учета",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": False,
                "district_field": "aoDistrictCode",
                "district_type": "code",
                "active": True
            },

            # Отчет по точкам учета (только округ, код)
            "report_metering_points": {
                "id": "27e9acfd-96c2-4e1b-a0cb-5119ff1a0f1a",
                "name": "Отчет по Точкам учета",
                "config": "meteringPointsPredBill",
                "group": "Точки учета",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": False,
                "district_field": "aoDistrictCode",
                "district_type": "code",
                "active": True
            },

            # Отчет о количестве строений с ПУ (с периодом, код округа, фиксированный формат "addressable")
            "report_buildings_with_md": {
                "id": "ca968bbf-61b9-42d9-9621-4e29ebe9397b",
                "name": "Отчет о количестве строений с ПУ",
                "config": "reportBuildingsWithMdCount",
                "group": "Строения",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": True,
                "has_format": True,
                "fixed_format": "addressable",
                "district_field": "aoCode",
                "district_type": "code",
                "active": True
            },

            # Отчет по приборам учета с просроченной поверкой (только округ, код)
            "report_expired_verification": {
                "id": "4476d128-8afe-4e40-927f-6ad38d2b5ea4",
                "name": "Отчет по приборам учета с просроченной поверкой",
                "config": "reportDevicesWithExpiredVerification",
                "group": "Поверка",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": False,
                "district_field": "aoCode",
                "district_type": "code",
                "active": True
            },

            # Отчет по сверке ОДПУ с данными ГИС ЖКХ (только округ, код)
            "report_gis_reconciliation": {
                "id": "779fa171-3619-4462-b0d2-40a908249633",
                "name": "Отчет по сверке ОДПУ с данными ГИС ЖКХ",
                "config": "reportMatchingGisZhKHDevices",
                "group": "ГИС ЖКХ",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": False,
                "district_field": "aoCode",
                "district_type": "code",
                "active": True
            },

            # Отчет о конфликтах показаний (с периодом и кодом округа)
            "report_readings_conflicts": {
                "id": "dd38afc8-6353-49fe-b776-c27602d5373f",
                "name": "Отчет зафиксированных конфликтов данных между показаниями приборов учета и отключенными установками",
                "config": "reportMdReadingsShutdownConflicts",
                "group": "Конфликты",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": True,
                "district_field": "aoCode",
                "district_type": "code",
                "active": True
            },

            # Отчет анализ показаний ОДУУ за 3 периода (с периодом и кодом округа)
            "report_oduu_analysis": {
                "id": "89a76842-89e9-442f-b607-28ab9451985d",
                "name": "Анализ показаний ОДУУ за 3 периода",
                "config": "reportMdReadingsThreeYearAnalysis",
                "group": "Аналитика",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": True,
                "district_field": "aoCode",
                "district_type": "code",
                "active": True
            },

            # Отчет по вводу показаний ПУ в разрезе муниципальных районов
            "report_metering_devices_by_municipal": {
                "id": "e3b7b84d-abd3-4142-b08e-292597d3a717",
                "name": "Отчет по вводу показаний ПУ в разрезе муниципальных районов",
                "config": "reportMeteringDevicesByMunicipalDistricts",
                "group": "Показания",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": True,
                "has_named_list": True,
                "district_field": "aoDistrictCode",
                "district_type": "code",
                "active": True
            },

            # Отчет о снятии показаний по точкам учета
            "report_metering_points_readings": {
                "id": "96327f88-1bf0-4ecc-ac85-2e4aa1b5700e",
                "name": "Отчет о снятии показаний по точкам учета",
                "config": "reportMeteringPointsReadings",
                "group": "Показания",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": True,
                "district_field": "aoDistrictCode",
                "district_type": "code",
                "active": True
            },

            # Отчет по температуре наружного воздуха
            "report_polygon_temperature": {
                "id": "ca5081fa-c479-4f4d-aa84-7188d4561864",
                "name": "Отчет по температуре наружного воздуха",
                "config": "reportPolygonTemperature",
                "group": "Погода",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": True,
                "district_field": "aoDistrictCode",
                "district_type": "code",
                "active": True
            },

            # Отчет о замене приборов учета МВК
            "report_replacement_metering_devices_mvk": {
                "id": "269ef220-015e-4854-85ed-bd4a10d7e30c",
                "name": "Отчет о замене приборов учета МВК",
                "config": "reportReplacementMeteringDevicesMVK",
                "group": "Замена ПУ",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": True,
                "district_field": "aoDistrictName",
                "district_type": "name",
                "active": True
            },

            # ========== НОВЫЕ ОТЧЕТЫ ==========
            # Отчет по запитке (с режимом "all")
            "report_supply_network": {
                "id": "7731218d-aafe-49cf-81c9-ba749588f6aa",
                "name": "Отчет по запитке",
                "config": "reportSupplyNetwork",
                "group": "Запитка",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": False,
                "has_report_mode": True,
                "fixed_report_mode": "all",
                "district_field": "aoCode",
                "district_type": "code",
                "active": True
            },

            # Отчет о переданных ведомостях за период (с startMonth и finishMonth)
            "report_transferred_statements": {
                "id": "cc04db32-f0ee-4ab6-aadd-2c6ebc6f3828",
                "name": "Отчет о переданных ведомостях за период",
                "config": "reportTransferredStatementsByPeriod",
                "group": "Ведомости",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period_range": True,
                "district_field": "aoCode",
                "district_type": "code",
                "active": True
            },

            # Отчет о передаче показаний в АС «Мосводоканал»
            "report_transmission_readings_mvk": {
                "id": "09ee1ef5-d3b6-40ff-bbd7-fb9ed2408801",
                "name": "Отчет о передаче показаний в АС «Мосводоканал»",
                "config": "reportTransmissionReadingsMVK",
                "group": "Показания",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": True,
                "district_field": "aoDistrictName",
                "district_type": "name",
                "active": True
            },

            # Активные показания ПУ не идущие в расчёт
            "report_unsuitable_md_readings": {
                "id": "4e3338ca-ec43-4395-a469-69fabe7f2a43",
                "name": "Активные показания ПУ не идущие в расчёт",
                "config": "reportUnsuitableMdReadings",
                "group": "Показания",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": True,
                "district_field": "aoCode",
                "district_type": "code",
                "active": True
            },

            # Отчет о результатах передачи данных через ЕЛК для водомеров
            "report_vodomer_elk": {
                "id": "2965c0c6-2818-45b8-9bf2-e1f153f81061",
                "name": "Отчет о результатах передачи данных через ЕЛК для водомеров",
                "config": "reportVodomerELK",
                "group": "Водомеры",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period_range": True,
                "district_field": "aoDistrictCode",
                "district_type": "code",
                "active": True
            },

            # Отчет по Сим-картам (без фильтров)
            "report_sim_cards": {
                "id": "67fa616b-69b6-425e-a400-bcec3753c00d",
                "name": "Отчет по Сим-картам",
                "config": "simCardsPredBill",
                "group": "Сим-карты",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": False,
                "has_district": False,
                "active": True
            },

            # Отчет по УСПД (без фильтров)
            "report_transmission_devices": {
                "id": "a1d15f84-7bcc-4b83-9ce6-c874a473203c",
                "name": "Отчет по УСПД",
                "config": "transmissionDevicesPredBill",
                "group": "УСПД",
                "endpoint": "/api/bear/script/sync/rabbitReportSender",
                "status_endpoint": "/api/bear/script/sync/getReportTaskStatus",
                "has_period": False,
                "has_district": False,
                "active": True
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
            "ROLE", "ROLE_ALL_OBJECTS", "ROLE_CHECK_DATA", "ROLE-TEST", "ROLE-TEST2",
            "TECHNOLOGICAL_DIVISION", "TECHNOLOGICAL_MANAGMENT", "TEST05122024", "WEATHER"
        ]

    def get_available_periods(self) -> List[str]:
        """
        Генерирует список доступных месяцев от января до предыдущего месяца от текущего
        Возвращает список строк в формате "ГГГГ-ММ-31" (последний день месяца)
        """
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month

        periods = []

        for month in range(1, current_month):
            if month == 12:
                last_day = 31
            else:
                next_month = datetime(current_year, month + 1, 1)
                last_day = (next_month - timedelta(days=1)).day

            period_str = f"{current_year}-{month:02d}-{last_day}"
            periods.append(period_str)

        return periods

    def get_random_period(self) -> str:
        """Возвращает случайный период из доступных"""
        periods = self.get_available_periods()
        return random.choice(periods)

    def get_random_period_range(self) -> Tuple[str, str]:
        """
        Возвращает случайный диапазон периодов (startMonth, finishMonth)
        startMonth не может быть младше finishMonth
        """
        periods = self.get_available_periods()
        if len(periods) < 2:
            # Если мало периодов, возвращаем один и тот же
            period = self.get_random_period()
            return period, period

        # Сортируем периоды
        sorted_periods = sorted(periods)
        # Выбираем случайный start индекс
        start_idx = random.randint(0, len(sorted_periods) - 2)
        # Выбираем случайный finish индекс, который >= start_idx
        finish_idx = random.randint(start_idx, len(sorted_periods) - 1)

        return sorted_periods[start_idx], sorted_periods[finish_idx]

    def get_random_district_name(self) -> List[str]:
        """Возвращает случайный административный округ (название)"""
        return [random.choice(self.AO_DISTRICT_NAMES)]

    def get_random_district_code(self) -> List[str]:
        """Возвращает случайный административный округ (код)"""
        return [random.choice(self.AO_DISTRICT_CODES)]

    def get_district_name_by_code(self, code: str) -> str:
        """Возвращает название округа по его коду"""
        return self.AO_CODE_TO_NAME.get(code, code)

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
            response = self.session.post(url, data=data, timeout=(self.REQUEST_TIMEOUT, 30))
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

    def send_report_request(self, report_key: str, retry_count: int = 0) -> Tuple[bool, Optional[str], float, Optional[Dict]]:
        """
        Отправка запроса на формирование отчета с retry-механизмом
        Возвращает: (успех, reportTaskId, время выполнения, детали ошибки)
        """
        report = self.REPORTS[report_key]

        print("\n" + "=" * 60)
        print(f"ЭТАП 2: ОТПРАВКА ЗАПРОСА НА ФОРМИРОВАНИЕ ОТЧЕТА")
        if retry_count > 0:
            print(f"ПОВТОРНАЯ ПОПЫТКА {retry_count}/{self.MAX_RETRIES}")
        print("=" * 60)

        url = f"{self.base_url}{report['endpoint']}"
        error_details = None

        # Выбираем случайные параметры для отчета
        period = None
        start_month = None
        finish_month = None
        district = None
        district_display = None
        report_format = None
        named_list = None
        report_mode = None

        # Обработка периода
        if report.get('has_period_range', False):
            start_month, finish_month = self.get_random_period_range()
        elif report.get('has_period', True):
            period = self.get_random_period()

        # Обработка округа
        if report.get('has_district', True):
            if report['district_type'] == 'name':
                district = self.get_random_district_name()
                district_display = district[0]
            else:  # code
                code = self.get_random_district_code()[0]
                district = [code]
                district_display = self.get_district_name_by_code(code)

        # Обработка формата
        if report.get('has_format', False):
            if report.get('fixed_format'):
                report_format = report['fixed_format']
            else:
                report_format = self.get_random_report_format()

        # Обработка чекбокса "перечень ПУ"
        if report.get('has_named_list', False):
            named_list = True

        # Обработка режима отчета
        if report.get('has_report_mode', False):
            if report.get('fixed_report_mode'):
                report_mode = report['fixed_report_mode']

        # Базовый events для всех отчетов
        report_events = {
            "start": {
                "id": "5383b779-48f9-4c97-8683-ac7df3c9707a",
                "dataTemplate": {
                    "fileName": "fileName",
                    "config": "config"
                }
            },
            "finish": {
                "id": "3678fef1-89ff-4340-b8c2-b3d42d736946",
                "dataTemplate": {
                    "name": "name",
                    "config": "config"
                }
            },
            "error": {
                "id": "2bc9aee9-f312-46fc-acd2-7c36b3730484",
                "dataTemplate": {
                    "name": "name",
                    "config": "config"
                }
            }
        }

        # Формируем фильтры отчета
        report_filters = {
            "dataRoles": self.DATA_ROLES
        }

        # Добавляем округ если нужно
        if district:
            report_filters[report['district_field']] = district

        # Добавляем период если нужно
        if period:
            report_filters["periodMonth"] = period

        # Добавляем диапазон периодов если нужно
        if start_month and finish_month:
            # Преобразуем в ISO формат с временем
            start_dt = datetime.strptime(start_month, '%Y-%m-%d')
            finish_dt = datetime.strptime(finish_month, '%Y-%m-%d')
            report_filters["startMonth"] = start_dt.replace(hour=20, minute=59, second=59).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            report_filters["finishMonth"] = finish_dt.replace(hour=20, minute=59, second=59).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        # Добавляем формат если нужно
        if report_format:
            report_filters["reportFormat"] = report_format

        # Добавляем чекбокс "перечень ПУ" если нужно
        if named_list:
            report_filters["namedListOfMD"] = named_list

        # Добавляем режим отчета если нужно
        if report_mode:
            report_filters["reportMode"] = report_mode

        # Для отчета по температуре наружного воздуха нужны dateFrom и dateUp
        if report_key == "report_polygon_temperature" and period:
            period_date = datetime.strptime(period, '%Y-%m-%d')
            date_from = period_date.replace(day=1).strftime('%Y-%m-%d')
            date_up = period_date.strftime('%Y-%m-%d')
            report_filters["dateFrom"] = date_from
            report_filters["dateUp"] = date_up

        # Для отчета о результатах передачи данных через ЕЛК для водомеров
        if report_key == "report_vodomer_elk" and start_month and finish_month:
            report_filters["dateFrom"] = start_month
            report_filters["dateUp"] = finish_month

        # Payload для отчета
        payload = {
            "dataRoles": self.DATA_ROLES,
            "reportInfo": {
                "reportId": report["id"],
                "authorId": 483,
                "reportConfig": report["config"],
                "reportEvents": json.dumps(report_events, ensure_ascii=False),
                "reportFilters": report_filters,
                "reportName": report["name"],
                "reportTemplate": "[]"
            }
        }

        print(f"Отправка запроса на формирование отчета...")
        print(f"  Отчет: {report['name']}")
        if period:
            print(f"  Период: {period}")
        if start_month and finish_month:
            print(f"  Период (диапазон): {start_month} - {finish_month}")
        if district:
            print(f"  Округ: {district_display}")
        if report_format:
            print(f"  Формат: {report_format}")
        if named_list:
            print(f"  Перечень ПУ: Включен")
        if report_mode:
            print(f"  Режим: {report_mode}")

        try:
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=(self.REQUEST_TIMEOUT, 180))
            response_time = time.time() - start_time

            if response.status_code == 200:
                response_data = response.json()
                report_task_id = response_data.get('reportTaskId')

                print(f"✓ ЗАПРОС ПРИНЯТ (200) [{response_time:.2f} сек]")
                print(f"  Сообщение: {response_data.get('message')}")
                print(f"  reportTaskId: {report_task_id}")

                # Сохраняем параметры запроса в результат
                request_data = {
                    "period": period,
                    "start_month": start_month,
                    "finish_month": finish_month,
                    "district": district_display,
                }
                if district:
                    request_data["district_code"] = district[0] if isinstance(district, list) else district
                if report_format:
                    request_data["format"] = report_format
                if named_list:
                    request_data["named_list"] = named_list
                if report_mode:
                    request_data["report_mode"] = report_mode

                return True, report_task_id, response_time, request_data
            elif response.status_code in [500, 502, 503, 504]:
                # Серверные ошибки - повторяем
                if retry_count < self.MAX_RETRIES:
                    print(f"  ⚠ Ошибка {response.status_code}, повторная попытка через {self.RETRY_DELAY} сек... (попытка {retry_count + 1}/{self.MAX_RETRIES})")
                    time.sleep(self.RETRY_DELAY)
                    return self.send_report_request(report_key, retry_count + 1)
                else:
                    error_details = {
                        "endpoint": report['endpoint'],
                        "status_code": response.status_code,
                        "response_body": response.text[:500],
                        "payload": payload,
                        "period": period,
                        "district": district_display,
                        "retry_count": retry_count
                    }
                    print(f"✗ ОШИБКА ОТПРАВКИ ЗАПРОСА: статус {response.status_code} [{response_time:.2f} сек] (после {self.MAX_RETRIES} попыток)")
                    print(f"  Тело ответа: {response.text[:200]}")
                    return False, None, response_time, error_details
            elif response.status_code == 409:
                # Конфликт - отчет уже в очереди
                error_details = {
                    "endpoint": report['endpoint'],
                    "status_code": response.status_code,
                    "response_body": response.text[:500],
                    "period": period,
                    "district": district_display,
                    "message": "Отчет уже в очереди"
                }
                print(f"✗ ОШИБКА ОТПРАВКИ ЗАПРОСА: статус {response.status_code} [{response_time:.2f} сек]")
                print(f"  Сообщение: Отчет с такими параметрами уже в очереди")
                return False, None, response_time, error_details
            else:
                error_details = {
                    "endpoint": report['endpoint'],
                    "status_code": response.status_code,
                    "response_body": response.text[:500],
                    "payload": payload,
                    "period": period,
                    "district": district_display
                }
                if report_format:
                    error_details["format"] = report_format
                print(f"✗ ОШИБКА ОТПРАВКИ ЗАПРОСА: статус {response.status_code} [{response_time:.2f} сек]")
                print(f"  Тело ответа: {response.text[:200]}")
                return False, None, response_time, error_details

        except requests.exceptions.Timeout:
            if retry_count < self.MAX_RETRIES:
                print(f"  ⚠ Таймаут, повторная попытка через {self.RETRY_DELAY} сек... (попытка {retry_count + 1}/{self.MAX_RETRIES})")
                time.sleep(self.RETRY_DELAY)
                return self.send_report_request(report_key, retry_count + 1)
            else:
                error_details = {
                    "endpoint": report['endpoint'],
                    "error_type": "TIMEOUT",
                    "message": f"Превышен таймаут соединения ({self.REQUEST_TIMEOUT} сек) после {self.MAX_RETRIES} попыток",
                    "period": period,
                    "district": district_display,
                    "retry_count": retry_count
                }
                print(f"✗ ТАЙМАУТ ПРИ ОТПРАВКЕ ЗАПРОСА (после {self.MAX_RETRIES} попыток)")
                return False, None, 0, error_details

        except requests.exceptions.ConnectionError:
            if retry_count < self.MAX_RETRIES:
                print(f"  ⚠ Ошибка подключения, повторная попытка через {self.RETRY_DELAY} сек... (попытка {retry_count + 1}/{self.MAX_RETRIES})")
                time.sleep(self.RETRY_DELAY)
                return self.send_report_request(report_key, retry_count + 1)
            else:
                error_details = {
                    "endpoint": report['endpoint'],
                    "error_type": "CONNECTION_ERROR",
                    "message": "Ошибка подключения к серверу после нескольких попыток",
                    "period": period,
                    "district": district_display,
                    "retry_count": retry_count
                }
                print(f"✗ ОШИБКА ПОДКЛЮЧЕНИЯ (после {self.MAX_RETRIES} попыток)")
                return False, None, 0, error_details

        except Exception as e:
            error_details = {
                "endpoint": report['endpoint'],
                "error_type": "EXCEPTION",
                "message": str(e),
                "traceback": traceback.format_exc(),
                "period": period,
                "district": district_display
            }
            if report_format:
                error_details["format"] = report_format
            print(f"✗ ОШИБКА: {str(e)}")
            return False, None, 0, error_details

    def check_report_status(self, report_key: str, report_task_id: str) -> Tuple[bool, Optional[str], float, Optional[Dict], Optional[Dict]]:
        """
        Проверка статуса формирования отчета
        Возвращает: (успех, статус, время выполнения, данные ответа, детали ошибки)
        """
        report = self.REPORTS[report_key]
        url = f"{self.base_url}{report['status_endpoint']}"
        error_details = None

        payload = {
            "dataRoles": self.DATA_ROLES,
            "id": report_task_id
        }

        try:
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=(self.REQUEST_TIMEOUT, 30))
            response_time = time.time() - start_time

            if response.status_code == 200:
                response_data = response.json()
                status = response_data.get('status')
                return True, status, response_time, response_data, None
            else:
                error_details = {
                    "endpoint": report['status_endpoint'],
                    "status_code": response.status_code,
                    "response_body": response.text[:500],
                    "report_task_id": report_task_id
                }
                return False, None, response_time, None, error_details

        except Exception as e:
            error_details = {
                "endpoint": report['status_endpoint'],
                "error_type": "EXCEPTION",
                "message": str(e),
                "report_task_id": report_task_id,
                "traceback": traceback.format_exc()
            }
            return False, None, 0, None, error_details

    def wait_for_report_ready(self, report_key: str, report_task_id: str, report_name: str) -> Tuple[bool, float, Optional[Dict], Optional[Dict]]:
        """
        Ожидание готовности отчета (статус READY)
        - Если на 2-й попытке статус QUEUED или NOT_FOUND - ждем 5 минут
        - В остальных случаях - ждем 10 минут
        Возвращает: (успех, общее время ожидания, финальные данные, детали ошибки)
        """
        print("\n" + "=" * 60)
        print(f"ЭТАП 3: ОЖИДАНИЕ ФОРМИРОВАНИЯ ОТЧЕТА")
        print(f"Отчет: {report_name}")
        print("=" * 60)

        # Флаг для определения сокращенного времени ожидания
        use_short_timeout = False
        SHORT_TIMEOUT = self.SHORT_WAIT_TIME  # 5 минут
        FULL_TIMEOUT = self.MAX_WAIT_TIME  # 10 минут

        print(f"Максимальное время ожидания: {FULL_TIMEOUT // 60} минут")

        start_wait = time.time()
        attempts = 0
        last_status = None
        first_status_shown = False
        processing_started = False
        short_timeout_triggered = False

        while True:
            attempts += 1
            elapsed = time.time() - start_wait

            # Проверяем не превышен ли таймаут
            current_timeout = SHORT_TIMEOUT if use_short_timeout else FULL_TIMEOUT
            if elapsed > current_timeout:
                timeout_minutes = current_timeout // 60
                error_details = {
                    "stage": "waiting",
                    "error_type": "TIMEOUT",
                    "message": f"Превышено максимальное время ожидания ({timeout_minutes} минут)",
                    "attempts": attempts,
                    "last_status": last_status,
                    "report_task_id": report_task_id,
                    "wait_time": elapsed,
                    "timeout_type": "short" if use_short_timeout else "full"
                }
                print(f"\n✗ ПРЕВЫШЕНО ВРЕМЯ ОЖИДАНИЯ ({timeout_minutes} минут)")
                return False, elapsed, None, error_details

            # Проверяем статус
            success, status, check_time, response_data, error_details = self.check_report_status(report_key, report_task_id)

            if not success:
                if not first_status_shown:
                    print(f"  Ожидание формирования отчета...", end="", flush=True)
                    first_status_shown = True
                time.sleep(self.POLL_INTERVAL)
                continue

            # Проверяем статус на 2-й попытке для активации сокращенного таймаута
            if attempts == 2 and not short_timeout_triggered:
                if status in ["QUEUED", "NOT_FOUND"]:
                    use_short_timeout = True
                    short_timeout_triggered = True
                    print(f"\n  ⚠ Обнаружен статус '{status}' на 2-й попытке. Сокращаем время ожидания до 5 минут.")
                    # Обновляем таймаут для текущей итерации
                    if elapsed > SHORT_TIMEOUT:
                        error_details = {
                            "stage": "waiting",
                            "error_type": "TIMEOUT",
                            "message": f"Превышено максимальное время ожидания (5 минут)",
                            "attempts": attempts,
                            "last_status": status,
                            "report_task_id": report_task_id,
                            "wait_time": elapsed,
                            "timeout_type": "short"
                        }
                        print(f"\n✗ ПРЕВЫШЕНО ВРЕМЯ ОЖИДАНИЯ (5 минут)")
                        return False, elapsed, None, error_details

            # Показываем первые два статуса для информации
            if not first_status_shown:
                print(f"  Попытка {attempts}: статус = {status}")
                first_status_shown = True
            elif attempts <= 2:
                print(f"  Попытка {attempts}: статус = {status}")

            # Если статус изменился на PROCESSING, показываем это один раз
            if status == "PROCESSING" and not processing_started and attempts > 2:
                print(f"  Формирование отчета...", end="", flush=True)
                processing_started = True

            # Если статус изменился и это финальный статус, показываем
            if status != last_status and attempts > 2 and status in ["READY", "ERROR"]:
                if processing_started:
                    print(f" готово!")
                print(f"  Попытка {attempts}: статус = {status} [{elapsed:.1f} сек]")

            last_status = status

            if status == "READY":
                duration = response_data.get('duration', {})
                print(f"\n✓ ОТЧЕТ СФОРМИРОВАН!")
                print(f"  Время формирования: {duration.get('min', 0)} мин {duration.get('sec', 0)} сек")
                return True, elapsed, response_data, None
            elif status == "ERROR":
                error_details = {
                    "stage": "formation",
                    "error_type": "FORMATION_ERROR",
                    "message": "Ошибка формирования отчета на стороне сервера",
                    "response_data": response_data,
                    "report_task_id": report_task_id
                }
                print(f"\n✗ ОШИБКА ФОРМИРОВАНИЯ ОТЧЕТА")
                return False, elapsed, response_data, error_details

            time.sleep(self.POLL_INTERVAL)

    def test_report(self, report_key: str) -> Dict[str, Any]:
        """Полный тест отчета со случайными параметрами"""
        report = self.REPORTS[report_key]

        if not report.get('active', False):
            return None

        print("\n" + "=" * 60)
        print(f"ТЕСТИРОВАНИЕ ФОРМИРОВАНИЯ ОТЧЕТА:")
        print(f"{report['name']}")
        print("=" * 60)

        start_time = time.time()
        result = {
            "key": report_key,
            "name": report["name"],
            "group": report["group"],
            "has_period": report.get('has_period', True),
            "has_period_range": report.get('has_period_range', False),
            "has_format": report.get('has_format', False),
            "has_named_list": report.get('has_named_list', False),
            "has_report_mode": report.get('has_report_mode', False),
            "has_district": report.get('has_district', True),
            "district_type": report.get('district_type', 'name'),
            "success": False,
            "report_task_id": None,
            "request_time": 0,
            "wait_time": 0,
            "total_time": 0,
            "status": None,
            "period": None,
            "start_month": None,
            "finish_month": None,
            "district": None,
            "format": None,
            "district_code": None,
            "named_list": None,
            "report_mode": None,
            "errors": []
        }

        request_success, report_task_id, request_time, request_data = self.send_report_request(report_key)
        result["request_time"] = request_time

        if request_data:
            result["period"] = request_data.get('period')
            result["start_month"] = request_data.get('start_month')
            result["finish_month"] = request_data.get('finish_month')
            result["district"] = request_data.get('district')
            result["format"] = request_data.get('format')
            result["district_code"] = request_data.get('district_code')
            result["named_list"] = request_data.get('named_list')
            result["report_mode"] = request_data.get('report_mode')

        if not request_success or not report_task_id:
            result["error"] = "Не удалось отправить запрос на формирование отчета"
            if isinstance(request_data, dict) and 'error_type' in request_data:
                result["errors"].append({"stage": "request", "details": request_data})
            return result

        result["report_task_id"] = report_task_id

        wait_success, wait_time, final_data, wait_error = self.wait_for_report_ready(report_key, report_task_id, report["name"])
        result["wait_time"] = wait_time
        result["total_time"] = time.time() - start_time

        if wait_success:
            result["success"] = True
            result["status"] = "READY"
            if final_data:
                result["duration"] = final_data.get('duration')
        else:
            result["status"] = "TIMEOUT/ERROR"
            result["error"] = "Отчет не сформирован за 10 минут"
            if wait_error:
                result["errors"].append({"stage": "waiting", "details": wait_error})

        print("\n" + "=" * 60)
        print("РЕЗУЛЬТАТ ТЕСТА")
        print("=" * 60)

        if result["success"]:
            print(f"✓ УСПЕХ: Отчет сформирован")
            print(f"  reportTaskId: {report_task_id}")
            if result.get('period'):
                print(f"  Период: {result['period']}")
            if result.get('start_month') and result.get('finish_month'):
                print(f"  Период (диапазон): {result['start_month']} - {result['finish_month']}")
            if result.get('district'):
                print(f"  Округ: {result['district']}")
            if result.get('format'):
                print(f"  Формат: {result['format']}")
            if result.get('named_list'):
                print(f"  Перечень ПУ: Включен")
            if result.get('report_mode'):
                print(f"  Режим: {result['report_mode']}")
            print(f"  Время запроса: {request_time:.2f} сек")
            print(f"  Время ожидания: {wait_time:.1f} сек")
            print(f"  Общее время: {result['total_time']:.1f} сек")
        else:
            print(f"✗ ОШИБКА: {result['error']}")
            print(f"  reportTaskId: {report_task_id}")
            if result.get('period'):
                print(f"  Период: {result['period']}")
            if result.get('start_month') and result.get('finish_month'):
                print(f"  Период (диапазон): {result['start_month']} - {result['finish_month']}")
            if result.get('district'):
                print(f"  Округ: {result['district']}")
            if result.get('format'):
                print(f"  Формат: {result['format']}")
            if result.get('named_list'):
                print(f"  Перечень ПУ: Включен")
            if result.get('report_mode'):
                print(f"  Режим: {result['report_mode']}")
            print(f"  Время запроса: {request_time:.2f} сек")
            print(f"  Время ожидания: {wait_time:.1f} сек")
            if result["errors"]:
                error = result['errors'][0]['details']
                if error.get('status_code'):
                    print(f"  HTTP статус: {error.get('status_code')}")
                if error.get('message'):
                    print(f"  Сообщение: {error.get('message')}")

        print("=" * 60)
        return result

    def run_all_tests(self):
        """Запуск всех активных тестов отчетов"""
        print("\n" + "=" * 80)
        print("ЗАПУСК ТЕСТИРОВАНИЯ ФОРМИРОВАНИЯ ОТЧЕТОВ")
        print("=" * 80)

        available_periods = self.get_available_periods()
        if available_periods:
            print(f"\nДоступные периоды для тестирования ({len(available_periods)} шт.):")
            for p in available_periods[:5]:  # Показываем только первые 5
                print(f"  • {p}")
            if len(available_periods) > 5:
                print(f"  ... и еще {len(available_periods) - 5}")

        active_reports = [(k, v) for k, v in self.REPORTS.items() if v.get('active', False)]
        print(f"\nАктивные отчеты ({len(active_reports)} шт.):")
        for key, report in active_reports:
            period_info = ""
            if report.get('has_period_range', False):
                period_info = "с диапазоном периодов"
            elif report.get('has_period', True):
                period_info = "с периодом"
            else:
                period_info = "без периода"
            district_info = "" if not report.get('has_district', True) else "с округом"
            format_info = f", формат: {report.get('fixed_format', 'случайный')}" if report.get('has_format') else ""
            named_list_info = ", с перечнем ПУ" if report.get('has_named_list') else ""
            print(f"  • {report['name']} - {period_info} {district_info}{format_info}{named_list_info}")

        if not self.authenticate():
            print("✗ ТЕСТИРОВАНИЕ ПРЕРВАНО: Ошибка авторизации")
            return

        start_time = time.time()
        self.results = []

        for i, (report_key, report) in enumerate(active_reports):
            print(f"\n{'=' * 80}")
            print(f"ТЕСТ {i+1} ИЗ {len(active_reports)}")
            print(f"{'=' * 80}")

            result = self.test_report(report_key)
            if result:
                self.results.append(result)

            if i < len(active_reports) - 1:
                print(f"\nПауза {self.PAUSE_BETWEEN_TESTS} секунды перед следующим отчетом...")
                time.sleep(self.PAUSE_BETWEEN_TESTS)

        self._print_final_report(start_time)

    def _print_final_report(self, start_time: float):
        """Вывод финального отчета"""
        print("\n" + "=" * 80)
        print("ФИНАЛЬНЫЙ ОТЧЕТ")
        print("=" * 80)

        total_time = time.time() - start_time
        minutes = int(total_time // 60)
        seconds = total_time % 60

        successful = sum(1 for r in self.results if r["success"])
        total = len(self.results)

        print(f"\nОБЩАЯ СТАТИСТИКА:")
        print(f"  Всего тестов: {total}")
        print(f"  Успешных: {successful}")
        print(f"  Проваленных: {total - successful}")
        print(f"  Процент успеха: {successful / total * 100:.1f}%")

        if minutes == 0:
            print(f"  Общее время: {seconds:.1f} секунд")
        else:
            print(f"  Общее время: {minutes} минут {seconds:.1f} секунд")

        failed_reports = [r for r in self.results if not r["success"]]
        if failed_reports:
            print(f"\n" + "=" * 80)
            print("ДЕТАЛЬНЫЙ РАЗБОР ОШИБОК")
            print("=" * 80)

            for r in failed_reports:
                print(f"\n❌ {r['name']}")
                if r.get('period'):
                    print(f"   Период: {r['period']}")
                if r.get('start_month') and r.get('finish_month'):
                    print(f"   Период (диапазон): {r['start_month']} - {r['finish_month']}")
                if r.get('district'):
                    print(f"   Округ: {r['district']}")
                if r.get('format'):
                    print(f"   Формат: {r['format']}")
                if r.get('named_list'):
                    print(f"   Перечень ПУ: Включен")
                if r.get('report_mode'):
                    print(f"   Режим: {r['report_mode']}")
                print(f"   reportTaskId: {r['report_task_id'] or 'не получен'}")
                print(f"   Ошибка: {r.get('error', 'Неизвестная ошибка')}")

                if r.get('errors'):
                    print(f"\n   Цепочка ошибок:")
                    for i, error in enumerate(r['errors'], 1):
                        print(f"     {i}. Этап: {error['stage']}")
                        details = error['details']
                        if details.get('status_code'):
                            print(f"        HTTP статус: {details['status_code']}")
                        if details.get('error_type'):
                            print(f"        Тип ошибки: {details['error_type']}")
                        if details.get('message'):
                            print(f"        Сообщение: {details['message']}")
                        if details.get('stage') == 'waiting' and details.get('attempts'):
                            print(f"        Попыток проверки: {details['attempts']}")
                            print(f"        Последний статус: {details.get('last_status', 'неизвестно')}")
                            print(f"        Время ожидания: {details.get('wait_time', 0):.1f} сек")

        else:
            print(f"\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО")
            print(f"\nПРОТЕСТИРОВАННЫЕ ОТЧЕТЫ ({total} шт.):\n")

            for r in self.results:
                period_info = f" (период: {r['period']})" if r.get('period') else ""
                range_info = f" (диапазон: {r['start_month']} - {r['finish_month']})" if r.get('start_month') and r.get('finish_month') else ""
                district_info = f", округ: {r['district']}" if r.get('district') else ""
                format_info = f", формат: {r['format']}" if r.get('format') else ""
                named_list_info = ", перечень ПУ: да" if r.get('named_list') else ""
                mode_info = f", режим: {r['report_mode']}" if r.get('report_mode') else ""
                time_info = f" - {r['wait_time']:.1f} сек"
                print(f"  • {r['name']}{period_info}{range_info}{district_info}{format_info}{named_list_info}{mode_info}{time_info}")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    tester = ReportTester(base_url="http://10.5.121.80:4980")
    tester.run_all_tests()