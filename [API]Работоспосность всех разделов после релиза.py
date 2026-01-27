import requests
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class SystemTester:
    def __init__(self, base_url: str = "http://10.5.121.74"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.results = []

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

        # Payload для потребления с checkVolumeMeasure
        self.consumption_payload = {
            "checkVolumeMeasure": "",
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
            "dateFrom": self.start_date.strftime("%Y-%m-%d")
        }

        # Payload для ЕКС НСИ: ЖУРНАЛ ОБМЕНА ДАННЫМИ
        self.eks_nsi_payload = self.common_payload.copy()
        self.eks_nsi_payload.update({
            "config": "eksNsiLogRegistrySql"
        })
        #Для отпуска тепловой энергии
        self.heat_release_payload = {
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
            "dateFrom": self.start_date.strftime("%Y-%m-%d")
        }

    def make_request(self, name: str, method: str, endpoint: str,
                     data: Optional[Dict] = None, headers: Optional[Dict] = None,
                     expected_status: int = 200) -> tuple:
        """
        Универсальный метод для выполнения запросов
        Возвращает: (успех, статус_код)
        """
        url = f"{self.base_url}{endpoint}"
        status_code = 0

        try:
            # Добавляем токен к заголовкам если он есть
            request_headers = headers or {}
            if self.token and 'Authorization' not in request_headers:
                request_headers['Authorization'] = f"Bearer {self.token}"

            # Выполняем запрос
            response = self.session.request(
                method=method,
                url=url,
                json=data if data else None,
                headers=request_headers,
                timeout=60
            )

            status_code = response.status_code

            # Проверяем статус код
            if response.status_code == expected_status:
                # Если это запрос за токеном, сохраняем его
                if endpoint == "/api/auth/token" and response.status_code == 200:
                    token_data = response.json()
                    self.token = token_data.get('token')
                return True, status_code
            else:
                return False, status_code

        except requests.exceptions.Timeout:
            return False, 408  # Таймаут
        except requests.exceptions.ConnectionError:
            return False, 0  # Ошибка подключения
        except Exception as e:
            return False, 500  # Другая ошибка

    def test_authentication(self) -> tuple:
        """Авторизация"""
        data = {
            "grant_type": "password",
            "username": "predbill",
            "password": "predbill"
        }

        success, status = self.make_request(
            name="АВТОРИЗАЦИЯ",
            method="POST",
            endpoint="/api/auth/token",
            data=data
        )

        if success:
            print(f"✓ АВТОРИЗАЦИЯ: OK (200)")
        else:
            print(f"✗ АВТОРИЗАЦИЯ: ОШИБКА ({status})")

        return success, status

    # Коммерческий учет
    def test_reestr_vedomostey(self) -> tuple:
        """Реестр ведомостей - POST запрос с данными"""
        params = {
            "page": 0,
            "size": 50,
            "sort": "dateFrom,desc"
        }

        success, status = self.make_request(
            name="РЕЕСТР ВЕДОМОСТЕЙ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/predBillingStatement",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ РЕЕСТР ВЕДОМОСТЕЙ: OK (200)")
        else:
            print(f"✗ РЕЕСТР ВЕДОМОСТЕЙ: ОШИБКА ({status})")

        return success, status

    def test_reestr_pokazaniy_vodomerov(self) -> tuple:
        """Реестр показаний водомеров - POST запрос"""
        success, status = self.make_request(
            name="РЕЕСТР ПОКАЗАНИЙ ВОДОМЕРОВ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/watermeterStatements",
            data=self.vpu_payload,  # Используем payload с dataSources
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ РЕЕСТР ПОКАЗАНИЙ ВОДОМЕРОВ: OK (200)")
        else:
            print(f"✗ РЕЕСТР ПОКАЗАНИЙ ВОДОМЕРОВ: ОШИБКА ({status})")

        return success, status

    def test_zagruzka_fayla_vpu(self) -> tuple:
        """Загрузка файла с данными по ВПУ - POST запрос"""
        success, status = self.make_request(
            name="ЗАГРУЗКА ФАЙЛА С ДАННЫМИ ПО ВПУ",
            method="POST",
            endpoint="/api/bear/script/sync/watermeterStatementsUpload",
            data=self.vpu_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ЗАГРУЗКА ФАЙЛА С ДАННЫМИ ПО ВПУ: OK (200)")
        else:
            print(f"✗ ЗАГРУЗКА ФАЙЛА С ДАННЫМИ ПО ВПУ: ОШИБКА ({status})")

        return success, status

    def test_upravlenie_blokirovkami(self) -> tuple:
        """Управление блокировками - POST запрос"""
        success, status = self.make_request(
            name="УПРАВЛЕНИЕ БЛОКИРОВКАМИ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/blocksManagement",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ УПРАВЛЕНИЕ БЛОКИРОВКАМИ: OK (200)")
        else:
            print(f"✗ УПРАВЛЕНИЕ БЛОКИРОВКАМИ: ОШИБКА ({status})")

        return success, status

    def test_varyiruemye_intervaly(self) -> tuple:
        """Варьируемые интервалы - POST запрос"""
        success, status = self.make_request(
            name="ВАРЬИРУЕМЫЕ ИНТЕРВАЛЫ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/variableIntervals",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ВАРЬИРУЕМЫЕ ИНТЕРВАЛЫ: OK (200)")
        else:
            print(f"✗ ВАРЬИРУЕМЫЕ ИНТЕРВАЛЫ: ОШИБКА ({status})")

        return success, status

    # Паспортизация и осблуживание
    def test_obekty_teplosetey(self) -> tuple:
        """Объекты теплосети - POST запрос"""
        success, status = self.make_request(
            name="ОБЪЕКТЫ ТЕПЛОСЕТИ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/accountingObjectsPredBill",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ОБЪЕКТЫ ТЕПЛОСЕТИ: OK (200)")
        else:
            print(f"✗ ОБЪЕКТЫ ТЕПЛОСЕТИ: ОШИБКА ({status})")

        return success, status

    def test_uzly_ucheta(self) -> tuple:
        """Узлы учета - POST запрос"""
        success, status = self.make_request(
            name="УЗЛЫ УЧЕТА",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/commercialNodes",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ УЗЛЫ УЧЕТА: OK (200)")
        else:
            print(f"✗ УЗЛЫ УЧЕТА: ОШИБКА ({status})")

        return success, status

    def test_reestr_ave_app(self) -> tuple:
        """Реестр АВЭ|АПП - POST запрос"""
        success, status = self.make_request(
            name="РЕЕСТР АВЭ|АПП",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/certificates",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ РЕЕСТР АВЭ|АПП: OK (200)")
        else:
            print(f"✗ РЕЕСТР АВЭ|АПП: ОШИБКА ({status})")

        return success, status

    def test_pribory_ucheta(self) -> tuple:
        """Приборы учета - POST запрос"""
        success, status = self.make_request(
            name="ПРИБОРЫ УЧЕТА",
            method="POST",
            endpoint="/api/bear/script/sync/flat/meteringDevicesPredBill",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ПРИБОРЫ УЧЕТА: OK (200)")
        else:
            print(f"✗ ПРИБОРЫ УЧЕТА: ОШИБКА ({status})")

        return success, status

    def test_sim_karty(self) -> tuple:
        """Sim-карты - POST запрос"""
        success, status = self.make_request(
            name="SIM-КАРТЫ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/simCardsPredBill",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ SIM-КАРТЫ: OK (200)")
        else:
            print(f"✗ SIM-КАРТЫ: ОШИБКА ({status})")

        return success, status

    def test_uspd(self) -> tuple:
        """УСПД - POST запрос"""
        success, status = self.make_request(
            name="УСПД",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/transmissionDevicesPredBill",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ УСПД: OK (200)")
        else:
            print(f"✗ УСПД: ОШИБКА ({status})")

        return success, status

    def test_shkaf_uspd(self) -> tuple:
        """Шкаф УСПД - POST запрос"""
        success, status = self.make_request(
            name="ШКАФ УСПД",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/cabineUspdsPredBill",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ШКАФ УСПД: OK (200)")
        else:
            print(f"✗ ШКАФ УСПД: ОШИБКА ({status})")

        return success, status

    # Технологический контроль
    def test_potreblenie(self) -> tuple:
        """Потребление - POST запрос"""
        success, status = self.make_request(
            name="ПОТРЕБЛЕНИЕ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/meteringPointsPredBill",
            data=self.consumption_payload,  # Используем специфичный payload с checkVolumeMeasure
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ПОТРЕБЛЕНИЕ: OK (200)")
        else:
            print(f"✗ ПОТРЕБЛЕНИЕ: ОШИБКА ({status})")

        return success, status

    def test_potreblenie_mvk(self) -> tuple:
        """Потребление МВК - POST запрос"""
        success, status = self.make_request(
            name="ПОТРЕБЛЕНИЕ МВК",
            method="POST",
            endpoint="/api/bear/script/sync/flat/consumptionMvk",
            data=self.consumption_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ПОТРЕБЛЕНИЕ МВК: OK (200)")
        else:
            print(f"✗ ПОТРЕБЛЕНИЕ МВК: ОШИБКА ({status})")

        return success, status

    def test_otpusk_teplovoy_energii(self) -> tuple:
        """Отпуск тепловой энергии - POST запрос"""
        success, status = self.make_request(
            name="ОТПУСК ТЕПЛОВОЙ ЭНЕРГИИ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/heatEnergyRelease",
            data=self.heat_release_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ОТПУСК ТЕПЛОВОЙ ЭНЕРГИИ: OK (200)")
        else:
            print(f"✗ ОТПУСК ТЕПЛОВОЙ ЭНЕРГИИ: ОШИБКА ({status})")

        return success, status

    def test_otklyucheniya(self) -> tuple:
        """Отключения - POST запрос"""
        success, status = self.make_request(
            name="ОТКЛЮЧЕНИЯ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/shutdownMeteringPoint",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ОТКЛЮЧЕНИЯ: OK (200)")
        else:
            print(f"✗ ОТКЛЮЧЕНИЯ: ОШИБКА ({status})")

        return success, status

    def test_vvod_dannyh_meteostanciy(self) -> tuple:
        """Ввод данных с метеостанций - POST запрос"""
        success, status = self.make_request(
            name="ВВОД ДАННЫХ С МЕТЕОСТАНЦИЙ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/weathersPredbill",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ВВОД ДАННЫХ С МЕТЕОСТАНЦИЙ: OK (200)")
        else:
            print(f"✗ ВВОД ДАННЫХ С МЕТЕОСТАНЦИЙ: ОШИБКА ({status})")

        return success, status

    def test_rezhimnye_karty(self) -> tuple:
        """Режимные карты - POST запрос"""
        success, status = self.make_request(
            name="РЕЖИМНЫЕ КАРТЫ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/modeCardsPredBill",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ РЕЖИМНЫЕ КАРТЫ: OK (200)")
        else:
            print(f"✗ РЕЖИМНЫЕ КАРТЫ: ОШИБКА ({status})")

        return success, status

    #  ИНТЕГРАЦИИ
    def test_asupr_zhurnal_polucheniya_vedomostey(self) -> tuple:
        """АСУПР: Журнал получения ведомостей - POST запрос"""
        success, status = self.make_request(
            name="АСУПР: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/statementUploadLogsRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АСУПР: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ: OK (200)")
        else:
            print(f"✗ АСУПР: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ: ОШИБКА ({status})")

        return success, status

    def test_asupr_zhurnal_polucheniya_spravochnikov(self) -> tuple:
        """АСУПР: Журнал получения справочников - POST запрос"""
        success, status = self.make_request(
            name="АСУПР: ЖУРНАЛ ПОЛУЧЕНИЯ СПРАВОЧНИКОВ",
            method="POST",
            endpoint="/api/bear/script/sync/flatBuff/directoryReceiptLogsRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АСУПР: ЖУРНАЛ ПОЛУЧЕНИЯ СПРАВОЧНИКОВ: OK (200)")
        else:
            print(f"✗ АСУПР: ЖУРНАЛ ПОЛУЧЕНИЯ СПРАВОЧНИКОВ: ОШИБКА ({status})")

        return success, status

    def test_asupr_zhurnal_sopostavleniya_spravochnikov(self) -> tuple:
        """АСУПР: Журнал сопоставления справочников - POST запрос"""
        success, status = self.make_request(
            name="АСУПР: ЖУРНАЛ СОПОСТАВЛЕНИЯ СПРАВОЧНИКОВ",
            method="POST",
            endpoint="/api/bear/script/sync/flatBuff/comparisonLogsMeteringUnitsRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АСУПР: ЖУРНАЛ СОПОСТАВЛЕНИЯ СПРАВОЧНИКОВ: OK (200)")
        else:
            print(f"✗ АСУПР: ЖУРНАЛ СОПОСТАВЛЕНИЯ СПРАВОЧНИКОВ: ОШИБКА ({status})")

        return success, status

    def test_elk_zhurnal_polucheniya_vedomostey(self) -> tuple:
        """ЕЛК: Журнал получения ведомостей - POST запрос"""
        success, status = self.make_request(
            name="ЕЛК: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/statementUploadLogsRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ЕЛК: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ: OK (200)")
        else:
            print(f"✗ ЕЛК: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ: ОШИБКА ({status})")

        return success, status

    def test_elk_poluchenie_dannyh_vpu(self) -> tuple:
        """ЕЛК: Получение данных из файла по ВПУ - POST запрос"""
        success, status = self.make_request(
            name="ЕЛК: ПОЛУЧЕНИЕ ДАННЫХ ИЗ ФАЙЛА ПО ВПУ",
            method="POST",
            endpoint="/api/bear/script/sync/watermeterStatementsUpload",
            data=self.vpu_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ЕЛК: ПОЛУЧЕНИЕ ДАННЫХ ИЗ ФАЙЛА ПО ВПУ: OK (200)")
        else:
            print(f"✗ ЕЛК: ПОЛУЧЕНИЕ ДАННЫХ ИЗ ФАЙЛА ПО ВПУ: ОШИБКА ({status})")

        return success, status

    def test_asot_zhurnal_polucheniya_dannyh(self) -> tuple:
        """АСОТ: Журнал получения данных - POST запрос"""
        success, status = self.make_request(
            name="АСОТ: ЖУРНАЛ ПОЛУЧЕНИЯ ДАННЫХ",
            method="POST",
            endpoint="/api/bear/script/sync/flatBuff/integration_asot_assd_query",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АСОТ: ЖУРНАЛ ПОЛУЧЕНИЯ ДАННЫХ: OK (200)")
        else:
            print(f"✗ АСОТ: ЖУРНАЛ ПОЛУЧЕНИЯ ДАННЫХ: ОШИБКА ({status})")

        return success, status

    def test_esm_zhurnal_vzaimodeystviya(self) -> tuple:
        """ЕСМ: Журнал взаимодействия - POST запрос"""
        success, status = self.make_request(
            name="ЕСМ: ЖУРНАЛ ВЗАИМОДЕЙСТВИЯ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/esmLogsRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ЕСМ: ЖУРНАЛ ВЗАИМОДЕЙСТВИЯ: OK (200)")
        else:
            print(f"✗ ЕСМ: ЖУРНАЛ ВЗАИМОДЕЙСТВИЯ: ОШИБКА ({status})")

        return success, status

    def test_mvk_zhurnal_vzaimodeystviya(self) -> tuple:
        """МВК: Журнал взаимодействия - POST запрос"""
        success, status = self.make_request(
            name="МВК: ЖУРНАЛ ВЗАИМОДЕЙСТВИЯ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/mvkLogsRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ МВК: ЖУРНАЛ ВЗАИМОДЕЙСТВИЯ: OK (200)")
        else:
            print(f"✗ МВК: ЖУРНАЛ ВЗАИМОДЕЙСТВИЯ: ОШИБКА ({status})")

        return success, status

    def test_assd_psd_zhurnal_polucheniya_vedomostey(self) -> tuple:
        """АССД ПСД: Журнал получения ведомостей - POST запрос"""
        success, status = self.make_request(
            name="АССД ПСД: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ",
            method="POST",
            endpoint="/api/bear/script/sync/flat/statementUploadLogsRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АССД ПСД: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ: OK (200)")
        else:
            print(f"✗ АССД ПСД: ЖУРНАЛ ПОЛУЧЕНИЯ ВЕДОМОСТЕЙ: ОШИБКА ({status})")

        return success, status

    def test_eks_nsi_zhurnal_obmena_dannymi(self) -> tuple:
        """ЕКС НСИ: Журнал обмена данными - POST запрос"""
        success, status = self.make_request(
            name="ЕКС НСИ: ЖУРНАЛ ОБМЕНА ДАННЫМИ",
            method="POST",
            endpoint="/api/bear/script/sync/eksNsiLogRegistry",
            data=self.eks_nsi_payload,  # Используем специфичный payload с config
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ЕКС НСИ: ЖУРНАЛ ОБМЕНА ДАННЫМИ: OK (200)")
        else:
            print(f"✗ ЕКС НСИ: ЖУРНАЛ ОБМЕНА ДАННЫМИ: ОШИБКА ({status})")

        return success, status

    def test_is_sbyt_obshchaya_statistika(self) -> tuple:
        """ИС СБЫТ: Общая статистика - POST запрос (две таблицы)"""
        # Первый запрос - kommSentLogs
        success1, status1 = self.make_request(
            name="ИС СБЫТ: ОБЩАЯ СТАТИСТИКА (kommSentLogs)",
            method="POST",
            endpoint="/api/bear/script/sync/flatBuff/kommSentLogs?page=0&size=50&sort=month_year,desc",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        # Второй запрос - kommIncomingLogs
        success2, status2 = self.make_request(
            name="ИС СБЫТ: ОБЩАЯ СТАТИСТИКА (kommIncomingLogs)",
            method="POST",
            endpoint="/api/bear/script/sync/flatBuff/kommIncomingLogs?page=0&size=50&sort=month_year,desc",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        # Общий результат считается успешным, если оба запроса успешны
        success = success1 and success2
        status = f"{status1}/{status2}"

        if success:
            print(f"✓ ИС СБЫТ: ОБЩАЯ СТАТИСТИКА: OK (200/200)")
        else:
            print(f"✗ ИС СБЫТ: ОБЩАЯ СТАТИСТИКА: ОШИБКА ({status})")

        return success, status

    def test_is_sbyt_zhurnal_oshibok(self) -> tuple:
        """ИС СБЫТ: Журнал ошибок - POST запрос"""
        success, status = self.make_request(
            name="ИС СБЫТ: ЖУРНАЛ ОШИБОК",
            method="POST",
            endpoint="/api/bear/script/sync/flatBuff/kommSentErrors",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ИС СБЫТ: ЖУРНАЛ ОШИБОК: OK (200)")
        else:
            print(f"✗ ИС СБЫТ: ЖУРНАЛ ОШИБОК: ОШИБКА ({status})")

        return success, status

    def test_zayavki_v_ukuike(self) -> tuple:
        """Заявки в УКУиКЭ - POST запрос"""
        success, status = self.make_request(
            name="ЗАЯВКИ В УКУИКЭ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/meteringDevicesApplicationTable",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ ЗАЯВКИ В УКУИКЭ: OK (200)")
        else:
            print(f"✗ ЗАЯВКИ В УКУИКЭ: ОШИБКА ({status})")

        return success, status

    def test_analitika_i_otchetnost(self) -> tuple:
        """Аналитика и отчетность - POST запрос"""
        success, status = self.make_request(
            name="АНАЛИТИКА И ОТЧЕТНОСТЬ",
            method="POST",
            endpoint="/api/bear/script/sync/getAnalyticsReportsByUser",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АНАЛИТИКА И ОТЧЕТНОСТЬ: OK (200)")
        else:
            print(f"✗ АНАЛИТИКА И ОТЧЕТНОСТЬ: ОШИБКА ({status})")

        return success, status

    def test_normativno_spravochnaya_informaciya(self) -> tuple:
        """Нормативно-справочная информация - POST запрос"""
        success, status = self.make_request(
            name="НОРМАТИВНО-СПРАВОЧНАЯ ИНФОРМАЦИЯ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/aoDistricts",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ НОРМАТИВНО-СПРАВОЧНАЯ ИНФОРМАЦИЯ: OK (200)")
        else:
            print(f"✗ НОРМАТИВНО-СПРАВОЧНАЯ ИНФОРМАЦИЯ: ОШИБКА ({status})")

        return success, status

    def test_administrirovanie_roli(self) -> tuple:
        """Администрирование: Роли - POST запрос"""
        success, status = self.make_request(
            name="АДМИНИСТРИРОВАНИЕ: РОЛИ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/roles",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АДМИНИСТРИРОВАНИЕ: РОЛИ: OK (200)")
        else:
            print(f"✗ АДМИНИСТРИРОВАНИЕ: РОЛИ: ОШИБКА ({status})")

        return success, status

    def test_administrirovanie_polzovateli(self) -> tuple:
        """Администрирование: Пользователи - POST запрос"""
        success, status = self.make_request(
            name="АДМИНИСТРИРОВАНИЕ: ПОЛЬЗОВАТЕЛИ",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/systemUsers",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АДМИНИСТРИРОВАНИЕ: ПОЛЬЗОВАТЕЛИ: OK (200)")
        else:
            print(f"✗ АДМИНИСТРИРОВАНИЕ: ПОЛЬЗОВАТЕЛИ: ОШИБКА ({status})")

        return success, status

    def test_administrirovanie_elementy_interfeysa(self) -> tuple:
        """Администрирование: Элементы интерфейса - POST запрос"""
        success, status = self.make_request(
            name="АДМИНИСТРИРОВАНИЕ: ЭЛЕМЕНТЫ ИНТЕРФЕЙСА",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/uiElements",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АДМИНИСТРИРОВАНИЕ: ЭЛЕМЕНТЫ ИНТЕРФЕЙСА: OK (200)")
        else:
            print(f"✗ АДМИНИСТРИРОВАНИЕ: ЭЛЕМЕНТЫ ИНТЕРФЕЙСА: ОШИБКА ({status})")

        return success, status

    def test_administrirovanie_planirovshchik(self) -> tuple:
        """Администрирование: Планировщик - POST запрос"""
        success, status = self.make_request(
            name="АДМИНИСТРИРОВАНИЕ: ПЛАНИРОВЩИК",
            method="POST",
            endpoint="/api/advanced/dynamic/data/flat/cronRegistry",
            data=self.common_payload,
            headers={'Content-Type': 'application/json'}
        )

        if success:
            print(f"✓ АДМИНИСТРИРОВАНИЕ: ПЛАНИРОВЩИК: OK (200)")
        else:
            print(f"✗ АДМИНИСТРИРОВАНИЕ: ПЛАНИРОВЩИК: ОШИБКА ({status})")

        return success, status

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("=" * 60)
        print("ТЕСТИРОВАНИЕ РЕАЛЬНЫХ POST ЗАПРОСОВ")
        print(f"Период: {self.start_date.strftime('%Y-%m-%d')} - {self.end_date.strftime('%Y-%m-%d')}")
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
            success, status = test_func()
            self.results.append((test_name, success, status))
            time.sleep(0.5)  # Пауза между запросами

        # Вывод финального отчета
        self._print_final_report(start_time)

    def _print_final_report(self, start_time):
        """Вывод финального отчета"""
        print("\n" + "=" * 60)
        print("ФИНАЛЬНЫЙ ОТЧЕТ")
        print("=" * 60)

        successful = 0
        failed_tests = []

        for test_name, success, status in self.results:
            if success:
                successful += 1
            else:
                failed_tests.append((test_name, status))

        total = len(self.results)

        print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"   Всего тестов: {total}")
        print(f"   Успешных: {successful}")
        print(f"   Проваленных: {len(failed_tests)}")

        if total > 0:
            print(f"   Процент успеха: {successful / total * 100:.1f}%")

        print(f"   Общее время: {time.time() - start_time:.2f} секунд")

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


# =========== ЗАПУСК ПРОГРАММЫ ===========
if __name__ == "__main__":
    # Создаем тестер
    tester = SystemTester(base_url="http://10.5.121.74")

    # Запускаем все тесты
    tester.run_all_tests()