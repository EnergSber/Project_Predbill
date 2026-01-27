"""
АВТОМАТИЗИРОВАННЫЙ ТЕСТЕР API СИСТЕМЫ "Предбиллинг"

Описание:
------------
Данный скрипт предназначен для комплексного тестирования REST API .
Проводим смоук тест всех разделов системы

Основные функции:
------------
1. Автоматическая авторизация в системе по логину/паролю
2. Последовательный тест 35+ разделов системы:
   - Коммерческий учет (ведомости, водомеры, блокировки)
   - Паспортизация (объекты, узлы учета, приборы, УСПД)
   - Технологический контроль (потребление, отпуск энергии, отключения)
   - Интеграции (АСУПР, ЕЛК, АСОТ, ЕСМ, МВК и др.)
   - Аналитика и отчетность
   - Администрирование (роли, пользователи, планировщик)
3. Измерение времени выполнения каждого запроса
4. Генерация детального отчета с статистикой
5. Выявление самых медленных разделов (топ-3 по времени)

Особенности:
------------
- Использует специфичные payload для разных типов запросов
- Поддерживает раздельные таймауты на соединение (15с) и чтение (180с)
- Сохраняет токен аутентификации для последующих запросов
- Форматирует общее время в минутах и секундах
- Обрабатывает различные типы ошибок (таймауты, ошибки соединения)

Использование:
------------
python system_tester.py

Результат:
------------
Подробный консольный отчет с указанием успешных/проваленных тестов,
временем выполнения каждого запроса и общей статистикой тестирования.
"""







import requests
import time
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta


class SystemTester:
    def __init__(self, base_url: str = "http://10.5.121.74"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.results = []  # Теперь будет хранить (name, success, status, response_time)

        # Получаем даты для запросов (текущий месяц)
        self.end_date = datetime.now()
        self.start_date = self.end_date.replace(day=1) - timedelta(days=1)

        # Общий payload для всех разделов
        self.common_payload = {
            "dataRoles": [
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
            ],
            "startMonth": self.start_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "finishMonth": self.end_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        }

        # Payload для разделов с ВПУ (добавляем dataSources)
        self.vpu_payload = self.common_payload.copy()
        self.vpu_payload.update({
            "dataSources": ["ASSD", "ManualLoad", "ManualLoadVPU"]
        })

        # Базовый payload для разделов с dateFrom
        self.date_from_payload = {
            "dataRoles": self.common_payload["dataRoles"],
            "dateFrom": self.start_date.strftime("%Y-%m-%d"),
            "startMonth": self.start_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "finishMonth": self.end_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        }

        # Payload для потребления с checkVolumeMeasure
        self.consumption_payload = self.date_from_payload.copy()
        self.consumption_payload.update({
            "checkVolumeMeasure": ""
        })

        # Payload для отпуска тепловой энергии (без checkVolumeMeasure)
        self.heat_release_payload = self.date_from_payload.copy()

        # Payload для ЕКС НСИ: ЖУРНАЛ ОБМЕНА ДАННЫМИ
        self.eks_nsi_payload = self.common_payload.copy()
        self.eks_nsi_payload.update({
            "config": "eksNsiLogRegistrySql"
        })

    def make_request(self, name: str, method: str, endpoint: str,
                     data: Optional[Dict] = None, headers: Optional[Dict] = None,
                     expected_status: int = 200) -> Tuple[bool, int, float]:
        """
        Универсальный метод для выполнения запросов с замером времени
        Возвращает: (успех, статус_код, время_выполнения)
        """
        url = f"{self.base_url}{endpoint}"
        status_code = 0
        response_time = 0.0

        try:
            # Добавляем токен к заголовкам если он есть
            request_headers = headers or {}
            if self.token and 'Authorization' not in request_headers:
                request_headers['Authorization'] = f"Bearer {self.token}"

            # Замер времени выполнения
            start_time = time.time()

            # Выполняем запрос
            response = self.session.request(
                method=method,
                url=url,
                json=data if data else None,
                headers=request_headers,
                timeout=(15, 180)
            )

            response_time = time.time() - start_time
            status_code = response.status_code

            # Проверяем статус код
            if response.status_code == expected_status:
                # Если это запрос за токеном, сохраняем его
                if endpoint == "/api/auth/token" and response.status_code == 200:
                    token_data = response.json()
                    self.token = token_data.get('token')
                return True, status_code, response_time
            else:
                return False, status_code, response_time

        except requests.exceptions.Timeout:
            return False, 408, response_time  # Таймаут
        except requests.exceptions.ConnectionError:
            return False, 0, response_time  # Ошибка подключения
        except Exception as e:
            return False, 500, response_time  # Другая ошибка

    def test_authentication(self) -> Tuple[bool, int, float]:
        """Авторизация"""
        data = {
            "grant_type": "password",
            "username": "predbill",
            "password": "predbill"
        }

        success, status, response_time = self.make_request(
            name="АВТОРИЗАЦИЯ",
            method="POST",
            endpoint="/api/auth/token",
            data=data
        )

        if success:
            print(f"✓ АВТОРИЗАЦИЯ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ АВТОРИЗАЦИЯ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    # Коммерческий учет
    def test_reestr_vedomostey(self) -> Tuple[bool, int, float]:
        """Реестр ведомостей - POST запрос с данными"""
        success, status, response_time = self.make_request(
            name="РЕЕСТР ВЕДОМОСТЕЙ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/predBillingStatement",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ РЕЕСТР ВЕДОМОСТЕЙ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ РЕЕСТР ВЕДОМОСТЕЙ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_reestr_pokazaniy_vodomerov(self) -> Tuple[bool, int, float]:
        """Реестр показаний водомеров - POST запрос"""
        success, status, response_time = self.make_request(
            name="РЕЕСТР ПОКАЗАНИЙ ВОДОМЕРОВ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/watermeterStatements",
            data=self.vpu_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ РЕЕСТР ПОКАЗАНИЙ ВОДОМЕРОВ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ РЕЕСТР ПОКАЗАНИЙ ВОДОМЕРОВ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_zagruzka_fayla_vpu(self) -> Tuple[bool, int, float]:
        """Загрузка файла с данными по ВПУ - POST запрос"""
        success, status, response_time = self.make_request(
            name="ЗАГРУЗКА ФАЙЛА С ДАННЫМИ ПО ВПУ",
            method="POST",
            endpoint="/api/bear/script/sync/watermeterStatementsUpload",
            data=self.vpu_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ЗАГРУЗКА ФАЙЛА С ДАННЫМИ ПО ВПУ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ЗАГРУЗКА ФАЙЛА С ДАННЫМИ ПО ВПУ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_upravlenie_blokirovkami(self) -> Tuple[bool, int, float]:
        """Управление блокировками - POST запрос"""
        success, status, response_time = self.make_request(
            name="УПРАВЛЕНИЕ БЛОКИРОВКАМИ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/blocksManagement",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ УПРАВЛЕНИЕ БЛОКИРОВКАМИ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ УПРАВЛЕНИЕ БЛОКИРОВКАМИ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_varyiruemye_intervaly(self) -> Tuple[bool, int, float]:
        """Варьируемые интервалы - POST запрос"""
        success, status, response_time = self.make_request(
            name="ВАРЬИРУЕМЫЕ ИНТЕРВАЛЫ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/variableIntervals",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ВАРЬИРУЕМЫЕ ИНТЕРВАЛЫ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ВАРЬИРУЕМЫЕ ИНТЕРВАЛЫ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    # Паспортизация и обслуживание
    def test_obekty_teplosetey(self) -> Tuple[bool, int, float]:
        """Объекты теплосети - POST запрос"""
        success, status, response_time = self.make_request(
            name="ОБЪЕКТЫ ТЕПЛОСЕТИ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/accountingObjectsPredBill",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ОБЪЕКТЫ ТЕПЛОСЕТИ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ОБЪЕКТЫ ТЕПЛОСЕТИ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_uzly_ucheta(self) -> Tuple[bool, int, float]:
        """Узлы учета - POST запрос"""
        success, status, response_time = self.make_request(
            name="УЗЛЫ УЧЕТА",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/commercialNodes",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ УЗЛЫ УЧЕТА: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ УЗЛЫ УЧЕТА: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_reestr_ave_app(self) -> Tuple[bool, int, float]:
        """Реестр АВЭ|АПП - POST запрос"""
        success, status, response_time = self.make_request(
            name="РЕЕСТР АВЭ|АПП",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/certificates",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ РЕЕСТР АВЭ|АПП: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ РЕЕСТР АВЭ|АПП: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_pribory_ucheta(self) -> Tuple[bool, int, float]:
        """Приборы учета - POST запрос"""
        success, status, response_time = self.make_request(
            name="ПРИБОРЫ УЧЕТА",
            method="POST",
            endpoint="/api/bear/script/sync/flat/meteringDevicesPredBill",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ПРИБОРЫ УЧЕТА: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ПРИБОРЫ УЧЕТА: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_sim_karty(self) -> Tuple[bool, int, float]:
        """Sim-карты - POST запрос"""
        success, status, response_time = self.make_request(
            name="SIM-КАРТЫ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/simCardsPredBill",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ SIM-КАРТЫ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ SIM-КАРТЫ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_uspd(self) -> Tuple[bool, int, float]:
        """УСПД - POST запрос"""
        success, status, response_time = self.make_request(
            name="УСПД",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/transmissionDevicesPredBill",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ УСПД: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ УСПД: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_shkaf_uspd(self) -> Tuple[bool, int, float]:
        """Шкаф УСПД - POST запрос"""
        success, status, response_time = self.make_request(
            name="ШКАФ УСПД",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/cabineUspdsPredBill",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ШКАФ УСПД: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ШКАФ УСПД: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    # Технологический контроль
    def test_potreblenie(self) -> Tuple[bool, int, float]:
        """Потребление - POST запрос"""
        success, status, response_time = self.make_request(
            name="ПОТРЕБЛЕНИЕ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/meteringPointsPredBill",
            data=self.consumption_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ПОТРЕБЛЕНИЕ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ПОТРЕБЛЕНИЕ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_potreblenie_mvk(self) -> Tuple[bool, int, float]:
        """Потребление МВК - POST запрос"""
        success, status, response_time = self.make_request(
            name="ПОТРЕБЛЕНИЕ МВК",
            method="POST",
            endpoint="/api/bear/script/sync/flat/consumptionMvk",
            data=self.consumption_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ПОТРЕБЛЕНИЕ МВК: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ПОТРЕБЛЕНИЕ МВК: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_otpusk_teplovoy_energii(self) -> Tuple[bool, int, float]:
        """Отпуск тепловой энергии - POST запрос"""
        success, status, response_time = self.make_request(
            name="ОТПУСК ТЕПЛОВОЙ ЭНЕРГИИ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/heatEnergyRelease",
            data=self.heat_release_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ОТПУСК ТЕПЛОВОЙ ЭНЕРГИИ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ОТПУСК ТЕПЛОВОЙ ЭНЕРГИИ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_otklyucheniya(self) -> Tuple[bool, int, float]:
        """Отключения - POST запрос"""
        success, status, response_time = self.make_request(
            name="ОТКЛЮЧЕНИЯ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/shutdownMeteringPoint",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ОТКЛЮЧЕНИЯ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ОТКЛЮЧЕНИЯ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_vvod_dannyh_meteostanciy(self) -> Tuple[bool, int, float]:
        """Ввод данных с метеостанций - POST запрос"""
        success, status, response_time = self.make_request(
            name="ВВОД ДАННЫХ С МЕТЕОСТАНЦИЙ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/weathersPredbill",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ВВОД ДАННЫХ С МЕТЕОСТАНЦИЙ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ВВОД ДАННЫХ С МЕТЕОСТАНЦИЙ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_rezhimnye_karty(self) -> Tuple[bool, int, float]:
        """Режимные карты - POST запрос"""
        success, status, response_time = self.make_request(
            name="РЕЖИМНЫЕ КАРТЫ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/modeCardsPredBill",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ РЕЖИМНЫЕ КАРТЫ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ РЕЖИМНЫЕ КАРТЫ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    # Интеграции
    def test_asupr_zhurnal_polucheniya_vedomostey(self) -> Tuple[bool, int, float]:
        """АСУПР: Журнал получения ведомостей - POST запрос"""
        success, status, response_time = self.make_request(
            name="АСУПР: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/statementUploadLogsRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АСУПР: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ АСУПР: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_asupr_zhurnal_polucheniya_spravochnikov(self) -> Tuple[bool, int, float]:
        """АСУПР: Журнал получения справочников - POST запрос"""
        success, status, response_time = self.make_request(
            name="АСУПР: ЖУРНАЛ ПОЛУЧЕНИЯ СПРАВОЧНИКОВ",
            method="POST",
            endpoint="/api/bear/script/sync/flatBuff/directoryReceiptLogsRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АСУПР: ЖУРНАЛ ПОЛУЧЕНИЯ СПРАВОЧНИКОВ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ АСУПР: ЖУРНАЛ ПОЛУЧЕНИЯ СПРАВОЧНИКОВ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_asupr_zhurnal_sopostavleniya_spravochnikov(self) -> Tuple[bool, int, float]:
        """АСУПР: Журнал сопоставления справочников - POST запрос"""
        success, status, response_time = self.make_request(
            name="АСУПР: ЖУРНАЛ СОПОСТАВЛЕНИЯ СПРАВОЧНИКОВ",
            method="POST",
            endpoint="/api/bear/script/sync/flatBuff/comparisonLogsMeteringUnitsRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АСУПР: ЖУРНАЛ СОПОСТАВЛЕНИЯ СПРАВОЧНИКОВ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ АСУПР: ЖУРНАЛ СОПОСТАВЛЕНИЯ СПРАВОЧНИКОВ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_elk_zhurnal_polucheniya_vedomostey(self) -> Tuple[bool, int, float]:
        """ЕЛК: Журнал получения ведомостей - POST запрос"""
        success, status, response_time = self.make_request(
            name="ЕЛК: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/statementUploadLogsRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ЕЛК: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ЕЛК: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_elk_poluchenie_dannyh_vpu(self) -> Tuple[bool, int, float]:
        """ЕЛК: Получение данных из файла по ВПУ - POST запрос"""
        success, status, response_time = self.make_request(
            name="ЕЛК: ПОЛУЧЕНИЕ ДАННЫХ ИЗ ФАЙЛА ПО ВПУ",
            method="POST",
            endpoint="/api/bear/script/sync/watermeterStatementsUpload",
            data=self.vpu_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ЕЛК: ПОЛУЧЕНИЕ ДАННЫХ ИЗ ФАЙЛА ПО ВПУ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ЕЛК: ПОЛУЧЕНИЕ ДАННЫХ ИЗ ФАЙЛА ПО ВПУ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_asot_zhurnal_polucheniya_dannyh(self) -> Tuple[bool, int, float]:
        """АСОТ: Журнал получения данных - POST запрос"""
        success, status, response_time = self.make_request(
            name="АСОТ: ЖУРНАЛ ПОЛУЧЕНИЯ ДАННЫХ",
            method="POST",
            endpoint="/api/bear/script/sync/flatBuff/integration_asot_assd_query",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АСОТ: ЖУРНАЛ ПОЛУЧЕНИЯ ДАННЫХ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ АСОТ: ЖУРНАЛ ПОЛУЧЕНИЯ ДАННЫХ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_esm_zhurnal_vzaimodeystviya(self) -> Tuple[bool, int, float]:
        """ЕСМ: Журнал взаимодействия - POST запрос"""
        success, status, response_time = self.make_request(
            name="ЕСМ: ЖУРНАЛ ВЗАИМОДЕЙСТВИЯ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/esmLogsRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ЕСМ: ЖУРНАЛ ВЗАИМОДЕЙСТВИЯ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ЕСМ: ЖУРНАЛ ВЗАИМОДЕЙСТВИЯ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_mvk_zhurnal_vzaimodeystviya(self) -> Tuple[bool, int, float]:
        """МВК: Журнал взаимодействия - POST запрос"""
        success, status, response_time = self.make_request(
            name="МВК: ЖУРНАЛ ВЗАИМОДЕЙСТВИЯ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/mvkLogsRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ МВК: ЖУРНАЛ ВЗАИМОДЕЙСТВИЯ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ МВК: ЖУРНАЛ ВЗАИМОДЕЙСТВИЯ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_assd_psd_zhurnal_polucheniya_vedomostey(self) -> Tuple[bool, int, float]:
        """АССД ПСД: Журнал получения ведомостей - POST запрос"""
        success, status, response_time = self.make_request(
            name="АССД ПСД: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/statementUploadLogsRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АССД ПСД: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ АССД ПСД: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_eks_nsi_zhurnal_obmena_dannymi(self) -> Tuple[bool, int, float]:
        """ЕКС НСИ: Журнал обмена данными - POST запрос"""
        success, status, response_time = self.make_request(
            name="ЕКС НСИ: ЖУРНАЛ ОБМЕНА ДАННЫМИ",
            method="POST",
            endpoint="/api/bear/script/sync/eksNsiLogRegistry",
            data=self.eks_nsi_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ЕКС НСИ: ЖУРНАЛ ОБМЕНА ДАННЫМИ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ЕКС НСИ: ЖУРНАЛ ОБМЕНА ДАННЫМИ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_is_sbyt_obshchaya_statistika(self) -> Tuple[bool, str, float]:
        """ИС СБЫТ: Общая статистика - POST запрос (две таблицы)"""
        total_time = 0.0

        # Первый запрос - kommSentLogs
        success1, status1, time1 = self.make_request(
            name="ИС СБЫТ: ОБЩАЯ СТАТИСТИКА (kommSentLogs)",
            method="POST",
            endpoint="/api/bear/script/sync/flatBuff/kommSentLogs?page=0&size=50&sort=month_year,desc",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )
        total_time += time1

        # Второй запрос - kommIncomingLogs
        success2, status2, time2 = self.make_request(
            name="ИС СБЫТ: ОБЩАЯ СТАТИСТИКА (kommIncomingLogs)",
            method="POST",
            endpoint="/api/bear/script/sync/flatBuff/kommIncomingLogs?page=0&size=50&sort=month_year,desc",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )
        total_time += time2

        # Общий результат считается успешным, если оба запроса успешны
        success = success1 and success2
        status = f"{status1}/{status2}"

        if success:
            print(f"✓ ИС СБЫТ: ОБЩАЯ СТАТИСТИКА: OK (200/200) [{total_time:.2f} сек]")
        else:
            print(f"✗ ИС СБЫТ: ОБЩАЯ СТАТИСТИКА: ОШИБКА ({status}) [{total_time:.2f} сек]")

        return success, status, total_time

    def test_is_sbyt_zhurnal_oshibok(self) -> Tuple[bool, int, float]:
        """ИС СБЫТ: Журнал ошибок - POST запрос"""
        success, status, response_time = self.make_request(
            name="ИС СБЫТ: ЖУРНАЛ ОШИБОК",
            method="POST",
            endpoint="/api/bear/script/sync/flatBuff/kommSentErrors",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ИС СБЫТ: ЖУРНАЛ ОШИБОК: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ИС СБЫТ: ЖУРНАЛ ОШИБОК: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_zayavki_v_ukuike(self) -> Tuple[bool, int, float]:
        """Заявки в УКУиКЭ - POST запрос"""
        success, status, response_time = self.make_request(
            name="ЗАЯВКИ В УКУИКЭ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/meteringDevicesApplicationTable",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ЗАЯВКИ В УКУИКЭ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ ЗАЯВКИ В УКУИКЭ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_analitika_i_otchetnost(self) -> Tuple[bool, int, float]:
        """Аналитика и отчетность - POST запрос"""
        success, status, response_time = self.make_request(
            name="АНАЛИТИКА И ОТЧЕТНОСТЬ",
            method="POST",
            endpoint="/api/bear/script/sync/getAnalyticsReportsByUser",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АНАЛИТИКА И ОТЧЕТНОСТЬ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ АНАЛИТИКА И ОТЧЕТНОСТЬ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_normativno_spravochnaya_informaciya(self) -> Tuple[bool, int, float]:
        """Нормативно-справочная информация - POST запрос"""
        success, status, response_time = self.make_request(
            name="НОРМАТИВНО-СПРАВОЧНАЯ ИНФОРМАЦИЯ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/aoDistricts",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ НОРМАТИВНО-СПРАВОЧНАЯ ИНФОРМАЦИЯ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ НОРМАТИВНО-СПРАВОЧНАЯ ИНФОРМАЦИЯ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_administrirovanie_roli(self) -> Tuple[bool, int, float]:
        """Администрирование: Роли - POST запрос"""
        success, status, response_time = self.make_request(
            name="АДМИНИСТРИРОВАНИЕ: РОЛИ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/roles",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АДМИНИСТРИРОВАНИЕ: РОЛИ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ АДМИНИСТРИРОВАНИЕ: РОЛИ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_administrirovanie_polzovateli(self) -> Tuple[bool, int, float]:
        """Администрирование: Пользователи - POST запрос"""
        success, status, response_time = self.make_request(
            name="АДМИНИСТРИРОВАНИЕ: ПОЛЬЗОВАТЕЛИ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/systemUsers",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АДМИНИСТРИРОВАНИЕ: ПОЛЬЗОВАТЕЛИ: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ АДМИНИСТРИРОВАНИЕ: ПОЛЬЗОВАТЕЛИ: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_administrirovanie_elementy_interfeysa(self) -> Tuple[bool, int, float]:
        """Администрирование: Элементы интерфейса - POST запрос"""
        success, status, response_time = self.make_request(
            name="АДМИНИСТРИРОВАНИЕ: ЭЛЕМЕНТЫ ИНТЕРФЕЙСА",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/uiElements",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АДМИНИСТРИРОВАНИЕ: ЭЛЕМЕНТЫ ИНТЕРФЕЙСА: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ АДМИНИСТРИРОВАНИЕ: ЭЛЕМЕНТЫ ИНТЕРФЕЙСА: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def test_administrirovanie_planirovshchik(self) -> Tuple[bool, int, float]:
        """Администрирование: Планировщик - POST запрос"""
        success, status, response_time = self.make_request(
            name="АДМИНИСТРИРОВАНИЕ: ПЛАНИРОВЩИК",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/cronRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АДМИНИСТРИРОВАНИЕ: ПЛАНИРОВЩИК: OK (200) [{response_time:.2f} сек]")
        else:
            print(f"✗ АДМИНИСТРИРОВАНИЕ: ПЛАНИРОВЩИК: ОШИБКА ({status}) [{response_time:.2f} сек]")

        return success, status, response_time

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("=" * 60)
        print("Тестирование POST запросов всех разделов")

        print("=" * 60)

        start_time = time.time()
        self.results = []  # Очищаем результаты

        # Запускаем тесты в порядке зависимостей
        tests = [
            ("АВТОРИЗАЦИЯ", self.test_authentication),

            # Коммерческий учет
            ("РЕЕСТР ВЕДОМОСТЕЙ", self.test_reestr_vedomostey),
            ("РЕЕСТР ПОКАЗАНИЙ ВОДОМЕРОВ", self.test_reestr_pokazaniy_vodomerov),
            ("ЗАГРУЗКА ФАЙЛА С ДАННЫМИ ПО ВПУ", self.test_zagruzka_fayla_vpu),
            ("УПРАВЛЕНИЕ БЛОКИРОВКАМИ", self.test_upravlenie_blokirovkami),
            ("ВАРЬИРУЕМЫЕ ИНТЕРВАЛЫ", self.test_varyiruemye_intervaly),

            # Паспортизация и обслуживание
            ("ОБЪЕКТЫ ТЕПЛОСЕТИ", self.test_obekty_teplosetey),
            ("УЗЛЫ УЧЕТА", self.test_uzly_ucheta),
            ("РЕЕСТР АВЭ|АПП", self.test_reestr_ave_app),
            ("ПРИБОРЫ УЧЕТА", self.test_pribory_ucheta),
            ("SIM-КАРТЫ", self.test_sim_karty),
            ("УСПД", self.test_uspd),
            ("ШКАФ УСПД", self.test_shkaf_uspd),

            # Технологический учет
            ("ПОТРЕБЛЕНИЕ", self.test_potreblenie),
            ("ПОТРЕБЛЕНИЕ МВК", self.test_potreblenie_mvk),
            ("ОТПУСК ТЕПЛОВОЙ ЭНЕРГИИ", self.test_otpusk_teplovoy_energii),
            ("ОТКЛЮЧЕНИЯ", self.test_otklyucheniya),
            ("ВВОД ДАННЫХ С МЕТЕОСТАНЦИЙ", self.test_vvod_dannyh_meteostanciy),
            ("РЕЖИМНЫЕ КАРТЫ", self.test_rezhimnye_karty),

            # Интеграции
            ("АСУПР: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ", self.test_asupr_zhurnal_polucheniya_vedomostey),
            ("АСУПР: ЖУРНАЛ ПОЛУЧЕНИЯ СПРАВОЧНИКОВ", self.test_asupr_zhurnal_polucheniya_spravochnikov),
            ("АСУПР: ЖУРНАЛ СОПОСТАВЛЕНИЯ СПРАВОЧНИКОВ", self.test_asupr_zhurnal_sopostavleniya_spravochnikov),
            ("ЕЛК: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ", self.test_elk_zhurnal_polucheniya_vedomostey),
            ("ЕЛК: ПОЛУЧЕНИЕ ДАННЫХ ИЗ ФАЙЛА ПО ВПУ", self.test_elk_poluchenie_dannyh_vpu),
            ("АСОТ: ЖУРНАЛ ПОЛУЧЕНИЯ ДАННЫХ", self.test_asot_zhurnal_polucheniya_dannyh),
            ("ЕСМ: ЖУРНАЛ ВЗАИМОДЕЙСТВИЯ", self.test_esm_zhurnal_vzaimodeystviya),
            ("МВК: ЖУРНАЛ ВЗАИМОДЕЙСТВИЯ", self.test_mvk_zhurnal_vzaimodeystviya),
            ("АССД ПСД: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ", self.test_assd_psd_zhurnal_polucheniya_vedomostey),
            ("ЕКС НСИ: ЖУРНАЛ ОБМЕНА ДАННЫМИ", self.test_eks_nsi_zhurnal_obmena_dannymi),
            ("ИС СБЫТ: ОБЩАЯ СТАТИСТИКА", self.test_is_sbyt_obshchaya_statistika),
            ("ИС СБЫТ: ЖУРНАЛ ОШИБОК", self.test_is_sbyt_zhurnal_oshibok),
            ("ЗАЯВКИ В УКУИКЭ", self.test_zayavki_v_ukuike),
            # Аналитика
            ("АНАЛИТИКА И ОТЧЕТНОСТЬ", self.test_analitika_i_otchetnost),

            # Нормативно-справочная информация
            ("НОРМАТИВНО-СПРАВОЧНАЯ ИНФОРМАЦИЯ", self.test_normativno_spravochnaya_informaciya),

            # Администрирование
            ("АДМИНИСТРИРОВАНИЕ: РОЛИ", self.test_administrirovanie_roli),
            ("АДМИНИСТРИРОВАНИЕ: ПОЛЬЗОВАТЕЛИ", self.test_administrirovanie_polzovateli),
            ("АДМИНИСТРИРОВАНИЕ: ЭЛЕМЕНТЫ ИНТЕРФЕЙСА", self.test_administrirovanie_elementy_interfeysa),
            ("АДМИНИСТРИРОВАНИЕ: ПЛАНИРОВЩИК", self.test_administrirovanie_planirovshchik),
        ]

        for test_name, test_func in tests:
            result = test_func()
            # Для совместимости с ИС СБЫТ (возвращает строку статуса)
            if len(result) == 3:
                success, status, response_time = result
            else:
                # Для старых методов (без времени)
                success, status = result
                response_time = 0.0

            self.results.append((test_name, success, status, response_time))
            time.sleep(0.5)  # Пауза между запросами

        # Вывод финального отчета
        self._print_final_report(start_time)

    def _print_final_report(self, start_time: float):
        """Вывод финального отчета с 3 самыми долгими разделами"""
        print("\n" + "=" * 60)
        print("ФИНАЛЬНЫЙ ОТЧЕТ")
        print("=" * 60)

        successful = 0
        failed_tests = []
        test_times = []

        for test_name, success, status, response_time in self.results:
            test_times.append((test_name, response_time))
            if success:
                successful += 1
            else:
                failed_tests.append((test_name, status))

        total = len(self.results)

        # Вычисляем общее время в минутах и секундах
        total_seconds = time.time() - start_time
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60

        print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"   Всего тестов: {total}")
        print(f"   Успешных: {successful}")
        print(f"   Проваленных: {len(failed_tests)}")

        if total > 0:
            print(f"   Процент успеха: {successful / total * 100:.1f}%")

        # Форматируем время в зависимости от продолжительности
        if minutes == 0:
            # Меньше минуты - показываем только секунды
            print(f"   Общее время: {seconds:.1f} секунд")
        elif seconds < 0.1:
            # Ровно N минут (без секунд)
            print(f"   Общее время: {minutes} минут")
        else:
            # Минуты и секунды
            print(f"   Общее время: {minutes} минут {seconds:.1f} секунд")

        # Топ-3 самых долгих разделов
        if test_times:
            test_times.sort(key=lambda x: x[1], reverse=True)
            top_slow = test_times[:3]

            print(f"3 САМЫХ ДОЛГИХ РАЗДЕЛОВ:")
            for i, (test_name, response_time) in enumerate(top_slow, 1):
                if response_time > 0:
                    print(f"   {i}. {test_name}: {response_time:.2f} сек")

        if failed_tests:
            print(f"\n🔴 ПРОВАЛЕННЫЕ ТЕСТЫ:")
            for test_name, status in failed_tests:
                if status == 0:
                    print(f"   • {test_name}: ОШИБКА ПОДКЛЮЧЕНИЯ")
                elif status == 408:
                    print(f"   • {test_name}: ТАЙМАУТ (408)")
                else:
                    print(f"   • {test_name}: КОД ОШИБКИ {status}")
        else:
            print(f"\n✅ ВСЕ ТЕСТЫ УСПЕШНЫ!")

        print("=" * 60)


#Запуск проги
if __name__ == "__main__":
    # Создаем тестер
    tester = SystemTester(base_url="http://10.5.121.74")

    # Запускаем все тесты
    tester.run_all_tests()