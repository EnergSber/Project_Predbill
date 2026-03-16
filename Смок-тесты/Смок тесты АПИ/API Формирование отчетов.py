'''ТЕСТ API "ФОРМИРОВАНИЕ ОТЧЕТОВ"

Описание:
------------
Скрипт для тестирования формирования отчетов через RabbitMQ
Постепенное добавление новых отчетов

Текущая версия: 8 отчетов
- Отчёт о проверке ведомостей (обобщенный)
- Отчёт о проверке ведомостей (детальный)
- Отчёт об обработке ведомостей за период
- Отчет по Приборам учета
- Отчет по Точкам учета
- Отчет о количестве строений с ПУ
- Отчет по приборам учета с просроченной поверкой
- Отчет по сверке ОДПУ с данными ГИС ЖКХ

Последовательность действий:
------------
1. Авторизация в системе
2. Для каждого отчета из конфигурации:
   - Выбираются случайные параметры (период и/или округ)
   - Отправка запроса на формирование отчета
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
    def __init__(self, base_url: str = "http://10.5.121.74"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.results = []

        # Максимальное время ожидания отчета (10 минут)
        self.MAX_WAIT_TIME = 600  # секунд
        self.POLL_INTERVAL = 1     # секунда
        self.PAUSE_BETWEEN_TESTS = 1  # пауза между отчетами 1 секунда

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

        # Форматы выгрузки для отчетов (оставляем для возможного расширения)
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
                "fixed_format": "addressable",  # Фиксированный формат - адресный перечень
                "district_field": "aoCode",
                "district_type": "code",
                "active": True
            },

            # Отчет по приборам учета с просроченной поверкой (только округ, код)
            "report_expired_verification": {
                "id": "e711c183-dfd2-4cf0-9a1c-fb19998bad12",
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

    def get_random_district_name(self) -> List[str]:
        """Возвращает случайный административный округ (название)"""
        return [random.choice(self.AO_DISTRICT_NAMES)]

    def get_random_district_code(self) -> List[str]:
        """Возвращает случайный административный округ (код)"""
        return [random.choice(self.AO_DISTRICT_CODES)]

    def get_random_report_format(self) -> str:
        """Возвращает случайный формат выгрузки (запасной метод)"""
        return random.choice(self.REPORT_FORMATS)

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

    def send_report_request(self, report_key: str) -> Tuple[bool, Optional[str], float, Optional[Dict]]:
        """
        Отправка запроса на формирование отчета
        Возвращает: (успех, reportTaskId, время выполнения, детали ошибки)
        """
        report = self.REPORTS[report_key]

        print("\n" + "=" * 60)
        print(f"ЭТАП 2: ОТПРАВКА ЗАПРОСА НА ФОРМИРОВАНИЕ ОТЧЕТА")
        print("=" * 60)

        url = f"{self.base_url}{report['endpoint']}"
        error_details = None

        # Выбираем случайные параметры для отчета
        period = None
        district = None
        district_display = None  # Для отображения (название)
        report_format = None

        if report.get('has_period', True):
            period = self.get_random_period()

        if report['district_type'] == 'name':
            district = self.get_random_district_name()
            district_display = district[0]  # Название
        else:  # code
            code = self.get_random_district_code()[0]
            district = [code]  # Для запроса отправляем код
            district_display = self.get_district_name_by_code(code)  # Для отображения название

        if report.get('has_format', False):
            if report.get('fixed_format'):
                report_format = report['fixed_format']  # Используем фиксированный формат
            else:
                report_format = self.get_random_report_format()  # Случайный выбор из доступных

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

        # Добавляем округ
        report_filters[report['district_field']] = district

        # Добавляем период если нужно
        if period:
            report_filters["periodMonth"] = period

        # Добавляем формат если нужно
        if report_format:
            report_filters["reportFormat"] = report_format

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
        print(f"  Округ: {district_display}")
        if report_format:
            print(f"  Формат: {report_format}")

        try:
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=(15, 30))
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
                    "district": district_display,
                }
                if report.get('district_type') == 'code':
                    request_data["district_code"] = district[0]
                if report_format:
                    request_data["format"] = report_format

                return True, report_task_id, response_time, request_data
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
            error_details = {
                "endpoint": report['endpoint'],
                "error_type": "TIMEOUT",
                "message": "Превышен таймаут соединения (15 сек)",
                "period": period,
                "district": district_display
            }
            if report_format:
                error_details["format"] = report_format
            print(f"✗ ТАЙМАУТ ПРИ ОТПРАВКЕ ЗАПРОСА")
            return False, None, 0, error_details

        except requests.exceptions.ConnectionError:
            error_details = {
                "endpoint": report['endpoint'],
                "error_type": "CONNECTION_ERROR",
                "message": "Ошибка подключения к серверу",
                "period": period,
                "district": district_display
            }
            if report_format:
                error_details["format"] = report_format
            print(f"✗ ОШИБКА ПОДКЛЮЧЕНИЯ")
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
            response = self.session.post(url, json=payload, timeout=(15, 30))
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
        Максимальное время ожидания: 10 минут
        Возвращает: (успех, общее время ожидания, финальные данные, детали ошибки)
        """
        print("\n" + "=" * 60)
        print(f"ЭТАП 3: ОЖИДАНИЕ ФОРМИРОВАНИЯ ОТЧЕТА")
        print(f"Отчет: {report_name}")
        print("=" * 60)

        print(f"Максимальное время ожидания: {self.MAX_WAIT_TIME // 60} минут")

        start_wait = time.time()
        attempts = 0
        last_status = None
        first_status_shown = False
        processing_started = False

        while True:
            attempts += 1
            elapsed = time.time() - start_wait

            # Проверяем не превышен ли таймаут
            if elapsed > self.MAX_WAIT_TIME:
                error_details = {
                    "stage": "waiting",
                    "error_type": "TIMEOUT",
                    "message": f"Превышено максимальное время ожидания ({self.MAX_WAIT_TIME // 60} минут)",
                    "attempts": attempts,
                    "last_status": last_status,
                    "report_task_id": report_task_id,
                    "wait_time": elapsed
                }
                print(f"\n✗ ПРЕВЫШЕНО ВРЕМЯ ОЖИДАНИЯ ({self.MAX_WAIT_TIME // 60} минут)")
                return False, elapsed, None, error_details

            # Проверяем статус
            success, status, check_time, response_data, error_details = self.check_report_status(report_key, report_task_id)

            if not success:
                if not first_status_shown:
                    print(f"  Ожидание формирования отчета...", end="", flush=True)
                    first_status_shown = True
                time.sleep(self.POLL_INTERVAL)
                continue

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

            # Ждем перед следующей попыткой
            time.sleep(self.POLL_INTERVAL)

    def test_report(self, report_key: str) -> Dict[str, Any]:
        """
        Полный тест отчета со случайными параметрами
        Возвращает результаты теста
        """
        report = self.REPORTS[report_key]

        # Пропускаем неактивные отчеты
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
            "has_format": report.get('has_format', False),
            "district_type": report.get('district_type', 'name'),
            "success": False,
            "report_task_id": None,
            "request_time": 0,
            "wait_time": 0,
            "total_time": 0,
            "status": None,
            "period": None,
            "district": None,
            "format": None,
            "district_code": None,
            "errors": []
        }

        # Шаг 1: Отправка запроса на формирование отчета
        request_success, report_task_id, request_time, request_data = self.send_report_request(report_key)
        result["request_time"] = request_time

        if request_data:
            result["period"] = request_data.get('period')
            result["district"] = request_data.get('district')
            result["format"] = request_data.get('format')
            result["district_code"] = request_data.get('district_code')

        if not request_success or not report_task_id:
            result["error"] = "Не удалось отправить запрос на формирование отчета"
            if isinstance(request_data, dict) and 'error_type' in request_data:
                result["errors"].append({
                    "stage": "request",
                    "details": request_data
                })
            return result

        result["report_task_id"] = report_task_id

        # Шаг 2: Ожидание готовности отчета
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
                result["errors"].append({
                    "stage": "waiting",
                    "details": wait_error
                })

        # Финальный вывод
        print("\n" + "=" * 60)
        print("РЕЗУЛЬТАТ ТЕСТА")
        print("=" * 60)

        if result["success"]:
            print(f"✓ УСПЕХ: Отчет сформирован")
            print(f"  reportTaskId: {report_task_id}")
            if result.get('period'):
                print(f"  Период: {result['period']}")
            if result.get('district'):
                print(f"  Округ: {result['district']}")
            if result.get('format'):
                print(f"  Формат: {result['format']}")
            print(f"  Время запроса: {request_time:.2f} сек")
            print(f"  Время ожидания: {wait_time:.1f} сек")
            print(f"  Общее время: {result['total_time']:.1f} сек")
        else:
            print(f"✗ ОШИБКА: {result['error']}")
            print(f"  reportTaskId: {report_task_id}")
            if result.get('period'):
                print(f"  Период: {result['period']}")
            if result.get('district'):
                print(f"  Округ: {result['district']}")
            if result.get('format'):
                print(f"  Формат: {result['format']}")
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

        # Показываем доступные периоды
        available_periods = self.get_available_periods()
        if available_periods:
            print(f"\nДоступные периоды для тестирования ({len(available_periods)} шт.):")
            for p in available_periods:
                print(f"  • {p}")

        # Показываем список активных отчетов
        active_reports = [(k, v) for k, v in self.REPORTS.items() if v.get('active', False)]
        print(f"\nАктивные отчеты ({len(active_reports)} шт.):")
        for key, report in active_reports:
            period_info = "с периодом" if report.get('has_period', True) else "без периода"
            format_info = f", формат: {report.get('fixed_format', 'случайный')}" if report.get('has_format') else ""
            print(f"  • {report['name']} - {period_info}{format_info}")

        # Шаг 1: Авторизация
        if not self.authenticate():
            print("✗ ТЕСТИРОВАНИЕ ПРЕРВАНО: Ошибка авторизации")
            return

        start_time = time.time()
        self.results = []

        # Тестируем каждый активный отчет
        for i, (report_key, report) in enumerate(active_reports):
            print(f"\n{'=' * 80}")
            print(f"ТЕСТ {i+1} ИЗ {len(active_reports)}")
            print(f"{'=' * 80}")

            result = self.test_report(report_key)
            if result:
                self.results.append(result)

            # Пауза между отчетами (1 секунда, кроме последнего)
            if i < len(active_reports) - 1:
                print(f"\nПауза {self.PAUSE_BETWEEN_TESTS} секунда перед следующим отчетом...")
                time.sleep(self.PAUSE_BETWEEN_TESTS)

        # Финальный отчет
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

        # Если есть ошибки - детальный разбор
        failed_reports = [r for r in self.results if not r["success"]]
        if failed_reports:
            print(f"\n" + "=" * 80)
            print("ДЕТАЛЬНЫЙ РАЗБОР ОШИБОК")
            print("=" * 80)

            for r in failed_reports:
                print(f"\n❌ {r['name']}")
                if r.get('period'):
                    print(f"   Период: {r['period']}")
                if r.get('district'):
                    print(f"   Округ: {r['district']}")
                if r.get('format'):
                    print(f"   Формат: {r['format']}")
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
                        if details.get('response_body'):
                            print(f"        Тело ответа: {details['response_body'][:200]}")
                        if details.get('stage') == 'waiting' and details.get('attempts'):
                            print(f"        Попыток проверки: {details['attempts']}")
                            print(f"        Последний статус: {details.get('last_status', 'неизвестно')}")
                            print(f"        Время ожидания: {details.get('wait_time', 0):.1f} сек")

        # Если ошибок нет - простой список отчетов
        else:
            print(f"\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО")
            print(f"\nПРОТЕСТИРОВАННЫЕ ОТЧЕТЫ ({total} шт.):\n")

            for r in self.results:
                period_info = f" (период: {r['period']})" if r.get('period') else ""
                district_info = f", округ: {r['district']}" if r.get('district') else ""
                format_info = f", формат: {r['format']}" if r.get('format') else ""
                time_info = f" - {r['wait_time']:.1f} сек"
                print(f"  • {r['name']}{period_info}{district_info}{format_info}{time_info}")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    # Создаем тестер и запускаем
    tester = ReportTester(base_url="http://10.5.121.74")
    tester.run_all_tests()