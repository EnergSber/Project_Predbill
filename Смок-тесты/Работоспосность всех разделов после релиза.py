'''ЦЕЛЬ: Комплексная проверка работоспособности всех разделов системы Predbilling.

ОПИСАНИЕ ТЕСТА:
1. АВТОРИЗАЦИЯ:
   - Вход в систему с учетными данными
   - Проверка успешного входа по изменению URL и сообщениям

2. ТЕСТИРОВАНИЕ РАЗДЕЛОВ (35 разделов)

ДЛЯ КАЖДОГО РАЗДЕЛА ПРОВЕРЯЕТСЯ:
1. Доступность раздела (переход по URL)
2. Отсутствие ошибок на странице (уведомления, алерты)
3. Работа фильтров (где применимо)
4. Наличие данных в таблицах
5. Умное ожидание исчезновения временных ошибок
6. Считаем время загрузки данных в каждом разделе

ОСОБЕННОСТИ:
- Поддержка 4 типов таблиц: default, komm_tables, analytics_tables, catalog_tables
- Автоматическое ожидание загрузки данных
- Обработка всплывающих сообщений об ошибках/успехе
- Подробный отчет с статистикой и списком ошибок


РЕЗУЛЬТАТ: Детальный отчет о работоспособности всех разделов системы'''


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from colorama import init, Fore, Back, Style

# Инициализация colorama для цветного вывода
init(autoreset=True)
# Хранение времени загрузки разделов
load_times = {}  # {section_name: {'start': time, 'end': time, 'duration': seconds}}
# Начало отсчета общего времени выполнения
total_script_start_time = time.time()

print("=" * 60)
print("Запуск")
print("=" * 60)

# Данные для авторизации
from config import USERNAME, PASSWORD
URL = 'http://10.5.121.74/login'

# Глобальные селекторы (одинаковые для всех разделов)
FILTER_SELECTOR = "svg[data-icon='filter']"
RESET_SELECTOR = "svg[data-icon='stop']"

# Селекторы таблиц для разных типов разделов
TABLE_SELECTORS = {
    'default': "#root > section > section > main > form > div > div > div > div:nth-child(1) > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body",
    'komm_tables': [
        ".BaseTable__body",  # Первый селектор для ИС СБЫТ раздела
        "div.BaseTable__body"  # Второй вариант для надежности ис сбыт
    ],
    'analytics_tables': [  # Новый тип для раздела Аналитика и отчетность
        ".BaseTable__body",  # Таблица со статусами отчетов
        ".ant-table-tbody",  # Таблица с доступными отчетами
        "div.rt-table .BaseTable__body"  # Дополнительный вариант
    ],
    'catalog_tables': [  # Новый тип для раздела Нормативно-Справочная информация
        ".CatalogData",  # Блок с сообщением "Выберите справочник"
        ".catalogList",  # Блок со списком справочников
        ".ant-collapse-item",  # Элементы аккордеона
        ".ant-collapse-header"  # Заголовки аккордеона
    ]
}

# Хранение результатов
all_errors = []  # Все уникальные ошибки
error_counter = {}  # Счетчик повторений ошибок
all_results = {}
total_errors_count = 0  # Общее количество ошибок


# Функции
def add_error(section_name, error_text, section_errors_list):
    """Добавить уникальную ошибку для раздела"""
    global total_errors_count

    # Проверяем, нет ли уже этой ошибки в списке ошибок раздела
    if error_text not in section_errors_list:
        section_errors_list.append(error_text)
        total_errors_count += 1
        print(f"ОШИБКА: {error_text}")

    return section_errors_list


def print_header(text):
    """Печать заголовка"""
    print(f"\n{'=' * 50}")
    print(f" {text}")
    print(f"{'=' * 50}")


def click_svg_element(svg_selector, action_name):
    """Кликнуть на SVG элемент через родительскую кнопку или JavaScript"""
    try:
        # Пробуем обычный способ
        svg_element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, svg_selector))
        )

        # Прокручиваем элемент в видимую область
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", svg_element)
        time.sleep(0.2)

        # Кликаем на родительскую кнопку
        parent_button = svg_element.find_element(By.XPATH, "..")
        parent_button.click()
        print(f"ВЫПОЛНЕНО: {action_name}")
        time.sleep(0.3)
        return True

    except Exception as e:
        print(f"НЕ УДАЛОСЬ {action_name}: {e}")

        # Пробуем через JavaScript
        try:
            element = driver.find_element(By.CSS_SELECTOR, svg_selector)
            driver.execute_script("arguments[0].click();", element)
            print(f"ВЫПОЛНЕНО: {action_name} (через JavaScript)")
            time.sleep(0.3)
            return True
        except:
            return False


def smart_wait_for_errors_disappear():
    """Умное ожидание исчезновения ошибок на странице с возможностью закрытия"""
    print(f"\nУмное ожидание исчезновения ошибок...")

    start_wait_time = time.time()
    max_wait_time = 5

    def try_close_error():
        """Пытается закрыть ошибку по крестику"""
        try:
            # Ищем кнопки закрытия ошибок
            close_selectors = [
                "span.ant-notification-notice-close-x",
                ".ant-notification-notice-close",
                ".ant-alert-close-icon",
                ".ant-message-notice-close",
                "[aria-label='close']",
                ".anticon-close"
            ]

            for selector in close_selectors:
                try:
                    close_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in close_buttons:
                        try:
                            if btn.is_displayed() or btn.is_enabled():
                                # Пробуем обычный клик
                                try:
                                    btn.click()
                                except:
                                    # Если не получается, пробуем через JavaScript
                                    driver.execute_script("arguments[0].click();", btn)

                                print(f"  Найден и кликнут крестик")
                                time.sleep(0.2)
                                return True
                        except:
                            # Пробуем клик через JavaScript даже если элемент не видим
                            try:
                                driver.execute_script("arguments[0].click();", btn)
                                print(f"  Кликнут крестик через JS")
                                time.sleep(0.2)
                                return True
                            except:
                                continue
                except:
                    continue

            # Пробуем найти по тексту "×" или "X"
            try:
                close_buttons = driver.find_elements(By.XPATH, "//*[text()='×' or text()='X' or text()='x']")
                for btn in close_buttons:
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                        print(f"  Кликнут крестик по тексту")
                        time.sleep(0.2)
                        return True
                    except:
                        continue
            except:
                pass

            return False

        except Exception as e:
            print(f"  Ошибка при попытке закрыть ошибку: {e}")
            return False


def wait_for_page_load(section_name):
    """Ожидание полной загрузки страницы с отслеживанием времени"""
    print("\nОжидание загрузки данных...")

    load_start = time.time()

    try:
        # Список CSS-селекторов для поиска элементов загрузки
        loading_selectors = [
            # Спиннер загрузки (кружок)
            "div.ant-spin.ant-spin-spinning",
            "div.ant-spin-spinning",

            # Текст "Загрузка..." в спиннере
            "div.ant-spin-text",

            # Иконка загрузки (крутящийся SVG)
            "span.anticon-loading.anticon-spin",
            "span.ant-spin-dot",

            # Контейнер спиннера
            "div.ant-spin-container"
        ]

        # Проверяем каждый селектор
        for selector in loading_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        if element.is_displayed():
                            element_class = element.get_attribute("class") or ""

                            # Если это спиннер
                            if ("ant-spin-spinning" in element_class or
                                    "anticon-spin" in element_class):
                                print(f"  Найден спиннер загрузки, ожидаем...")

                                # Ждем пока элемент станет невидимым
                                wait.until(EC.invisibility_of_element(element))
                                print(f"  Спиннер исчез")

                    except Exception as e:
                        continue
            except Exception as e:
                continue

        # Дополнительная проверка по XPath для текстовых сообщений в спиннере
        text_messages = [
            "Загрузка",
            "Обновление сопоставленных МВК",
            "Обновление данных"
        ]

        for text_msg in text_messages:
            try:
                elements = driver.find_elements(By.XPATH,
                                                f"//div[contains(@class, 'ant-spin-text') and contains(text(), '{text_msg}')]")
                for element in elements:
                    try:
                        if element.is_displayed():
                            print(f"  Ожидание исчезновения '{text_msg}'...")
                            wait.until(EC.invisibility_of_element(element))
                            print(f"  '{text_msg}' исчез")
                    except:
                        continue
            except:
                continue

        load_duration = time.time() - load_start
        print(f"Загрузка данных завершена за {load_duration:.1f} секунд")

        return load_duration

    except Exception as e:
        print(f"  Ошибка при ожидании загрузки: {e}")
        return time.time() - load_start

    def check_for_persistent_errors():
        """Проверяет наличие стойких ошибок, которые можно закрыть"""
        error_check_selectors = [
            "div.ant-notification-notice-error",
            "div.ant-alert-error",
            ".ant-message-error",
        ]

        for selector in error_check_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    try:
                        if elem.is_displayed():
                            error_text = elem.text.strip()
                            if error_text and len(error_text) > 3:
                                text_lower = error_text.lower()
                                if ("не обнаружено" not in text_lower and
                                        "не найдено" not in text_lower and
                                        "успешно" not in text_lower and
                                        "успешн" not in text_lower and
                                        "завершено" not in text_lower and
                                        "completed" not in text_lower and
                                        "готово" not in text_lower):
                                    return True
                    except:
                        continue
            except:
                continue
        return False

    try:
        # Ждем до 15 секунд пока ошибки не исчезнут
        while time.time() - start_wait_time < max_wait_time:
            # Проверяем, есть ли ошибки сейчас
            if check_for_persistent_errors():
                elapsed = time.time() - start_wait_time

                # Если ошибка держится больше 0.5 секунды, пытаемся закрыть
                if elapsed > 0.5:
                    print(f"  Ошибка держится {elapsed:.1f}с, пробуем закрыть...")
                    if try_close_error():
                        print(f"  Попытка закрытия выполнена")
                        time.sleep(0.5)
                    else:
                        print(f"  Не удалось найти кнопку закрытия")

                time.sleep(0.5)
            else:
                # Ошибок нет
                print(f"Ошибки исчезли")
                return True

        # Если вышли по таймауту
        print(f"Ошибки не исчезли за {max_wait_time} секунд, продолжаем...")
        return False

    except Exception as e:
        print(f"Исключение в умном ожидании: {e}")
        return False


# Выполнение теста

# Настройка браузера
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()
wait = WebDriverWait(driver, 60)

# Вход в систему
print_header("АВТОРИЗАЦИЯ")
try:
    driver.get(URL)

    username_field = wait.until(EC.presence_of_element_located((By.ID, "normal_login_username")))
    username_field.send_keys(USERNAME)

    password_field = driver.find_element(By.ID, "normal_login_password")
    password_field.send_keys(PASSWORD)

    driver.find_element(By.CSS_SELECTOR, '.ant-btn.ant-btn-primary.w-100.mb-s').click()

    # Проверка входа - ждем изменения URL
    wait.until_not(EC.url_contains('login'))
    print("Авторизация успешна (URL изменился)")

except Exception as e:
    print(f"Авторизация не удалась: {e}")


# Проверка раздела
def test_section(section_url, section_name, check_filters=True, table_type='default'):
    """Проверка раздела с опциональной проверкой фильтров и выбором типа таблицы"""
    print_header(f"ПРОВЕРКА: {section_name}")

    # Записываем время начала загрузки раздела (общее время тестирования раздела)
    section_start_time = time.time()
    load_times[section_name] = {'section_start': section_start_time}

    section_errors = []

    # Переход в раздел
    try:
        driver.get(section_url)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print(f"Переход в {section_name}")
        time.sleep(0.5)
    except Exception as e:
        section_errors = add_error(section_name, f"Не удалось перейти: {e}", section_errors)
        load_times[section_name]['section_end'] = time.time()
        load_times[section_name]['total_duration'] = load_times[section_name]['section_end'] - section_start_time
        return section_errors

    # Проверка ошибок на странице
    print("Поиск ошибок на странице...")

    # 1. Проверка по CSS-селекторам
    error_selectors = [
        "div.ant-notification-notice-error",
        "div.ant-alert-error",
        ".ant-message-error",
        "div > div > div > div.ant-notification-notice-message",
        "[class*='error']",
        "[class*='danger']",
        ".text-danger",
        ".ant-result-error"
    ]

    error_found = False
    for selector in error_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                try:
                    if elem.is_displayed():
                        error_text = elem.text.strip()
                        if error_text and len(error_text) > 3:
                            section_errors = add_error(section_name, error_text, section_errors)
                            error_found = True
                except:
                    continue
        except:
            continue

    if not error_found:
        print(f"Явных ошибок не найдено")
    else:
        # Вызываем умное ожидание с возможностью закрытия ошибок
        smart_wait_for_errors_disappear()

    # Работа с фильтрами
    filter_reset_time = None  # Время начала сброса фильтров

    if check_filters:
        print("\nРабота с фильтрами:")

        # Даем время странице полностью загрузиться
        time.sleep(0.5)

        # Открытие фильтра
        filter_clicked = False
        max_attempts = 3

        for attempt in range(max_attempts):
            if click_svg_element(FILTER_SELECTOR, f"Открыть фильтр (попытка {attempt + 1})"):
                filter_clicked = True
                break
            else:
                # Пробуем альтернативные селекторы
                alt_selectors = [
                    "[data-icon='filter']",
                    "svg[data-icon='filter']",
                    "button:has(svg[data-icon='filter'])",
                    "span:has(svg[data-icon='filter'])"
                ]

                for alt_selector in alt_selectors:
                    try:
                        element = driver.find_element(By.CSS_SELECTOR, alt_selector)
                        driver.execute_script("arguments[0].click();", element)
                        print(f"Открыть фильтр (через альтернативный селектор)")
                        filter_clicked = True
                        break
                    except:
                        continue

                if filter_clicked:
                    break

                time.sleep(0.5)

        if not filter_clicked:
            section_errors = add_error(section_name, "Не удалось открыть фильтр", section_errors)
        else:
            time.sleep(0.5)
            smart_wait_for_errors_disappear()

        # Сброс фильтров - ЗАПОМИНАЕМ ВРЕМЯ НАЧАЛА СБРОСА
        reset_clicked = False
        filter_reset_time = time.time()  # Запоминаем время начала сброса

        for attempt in range(max_attempts):
            if click_svg_element(RESET_SELECTOR, f"Сбросить фильтры (попытка {attempt + 1})"):
                reset_clicked = True
                break
            else:
                # Пробуем альтернативные селекторы
                alt_selectors = [
                    "[data-icon='stop']",
                    "svg[data-icon='stop']",
                    "button:has(svg[data-icon='stop'])",
                    "span:has(svg[data-icon='stop'])"
                ]

                for alt_selector in alt_selectors:
                    try:
                        element = driver.find_element(By.CSS_SELECTOR, alt_selector)
                        driver.execute_script("arguments[0].click();", element)
                        print(f"Сбросить фильтры (через альтернативный селектор)")
                        reset_clicked = True
                        break
                    except:
                        continue

                if reset_clicked:
                    break

                time.sleep(0.5)

        if not reset_clicked:
            section_errors = add_error(section_name, "Не удалось сбросить фильтры", section_errors)
            filter_reset_time = None  # Сбрасываем время, если сброс не удался

    # Проверка данных в таблице
    print("\nПроверка данных в таблице...")

    # Теперь ждем загрузку данных ПОСЛЕ сброса фильтров
    # Если был сброс фильтров, начинаем отсчет времени с момента сброса
    if check_filters and filter_reset_time:
        print(f"Ожидание загрузки после сброса фильтров...")
        load_start_time = filter_reset_time
    else:
        load_start_time = time.time()

    load_duration = wait_for_page_load(section_name)

    # Записываем время окончания загрузки
    load_end_time = time.time()

    # Сохраняем время загрузки после сброса
    load_times[section_name]['load_start'] = load_start_time
    load_times[section_name]['load_end'] = load_end_time
    load_times[section_name]['load_duration'] = load_duration

    # Также сохраняем общее время тестирования раздела
    section_end_time = time.time()
    load_times[section_name]['section_end'] = section_end_time
    load_times[section_name]['total_duration'] = section_end_time - section_start_time

    try:
        # Выбираем стратегию поиска таблицы в зависимости от типа
        if table_type in ['komm_tables', 'analytics_tables', 'catalog_tables']:
            found_elements = []
            element_selectors = TABLE_SELECTORS[table_type]

            for selector in element_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            found_elements.append(element)
                except:
                    continue

            if found_elements:
                print(f"Найдено элементов: {len(found_elements)}")
                total_data_items = 0

                for i, element in enumerate(found_elements, 1):
                    element_text = element.text.strip()

                    if table_type == 'catalog_tables':
                        if element_text and len(element_text) > 5:
                            total_data_items += 1

                    elif "BaseTable__body" in (element.get_attribute("class") or ""):
                        rows = element.find_elements(By.CSS_SELECTOR,
                                                     ".BaseTable__row, [role='row'], tr.ant-table-row, tr")
                        data_rows = []
                        for row in rows:
                            try:
                                row_text = row.text.strip()
                                if row_text and len(row_text) > 10:
                                    data_rows.append(row_text)
                            except:
                                continue

                        if data_rows:
                            print(f"    Данные в таблице #{i}: {len(data_rows)} строк")
                            total_data_items += len(data_rows)
                        else:
                            print(f"    Таблица #{i} пуста")

                    elif element_text and len(element_text) > 5:
                        total_data_items += 1

                if total_data_items == 0:
                    section_errors = add_error(section_name, "Нет данных в элементах", section_errors)
                else:
                    print(f"Всего найдено данных: {total_data_items}")

            else:
                section_errors = add_error(section_name, "Не найдены элементы", section_errors)

        else:
            # Стандартный поиск одной таблицы
            table_selector = TABLE_SELECTORS.get(table_type, TABLE_SELECTORS['default'])

            table_body = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, table_selector))
            )

            rows = table_body.find_elements(By.CSS_SELECTOR, ".BaseTable__row, tr")
            data_rows = []

            for row in rows:
                try:
                    row_text = row.text.strip()
                    if row_text and len(row_text) > 10:
                        data_rows.append(row_text)
                except:
                    continue

            if data_rows:
                print(f"Данные в таблице: {len(data_rows)} строк")
            else:
                section_errors = add_error(section_name, "Нет данных в таблице", section_errors)

    except Exception as e:
        section_errors = add_error(section_name, f"Ошибка проверки таблицы: {e}", section_errors)

    return section_errors


# Тест разделов
print_header("ТЕСТИРОВАНИЕ РАЗДЕЛОВ")

# Список разделов для проверки (с указанием нужно ли проверять фильтры и тип таблицы)
sections = [
    {
        'url': 'http://10.5.121.74/commercialControl/billingStatements',
        'name': 'Реестр ведомостей',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/commercialControl/watermeterStatements',
        'name': 'Реестр показаний водомеров',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/commercialControl/watermeterStatementUploadLog',
        'name': 'Загрузка файла с данными по ВПУ',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/commercialControl/blocksManagement',
        'name': 'Управление блокировками',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/commercialControl/variableIntervals',
        'name': 'Варьируемые интервалы',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/predbilling/accountingObjectsPredBill',
        'name': 'Объекты теплосети',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/predbilling/commercialNodes',
        'name': 'Узлы учета',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/predbilling/certificates',
        'name': 'Реестр АВЭ|АПП',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/predbilling/meteringDevicesPredBill',
        'name': 'Приборы учета',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/predbilling/simCardsPredBill',
        'name': 'Sim-карты',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/predbilling/transmissionDevicesPredBill',
        'name': 'УСПД',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/predbilling/cabineUspdsPredBill',
        'name': 'Шкаф УСПД',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/technicalControl/meteringPointsPredBill',
        'name': 'Потребление',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/technicalControl/consumptionMvk',
        'name': 'Потребление МВК',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/technicalControl/heatEnergyRelease',
        'name': 'Отпуск тепловой энергии',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/technicalControl/shutdownMeteringPoint',
        'name': 'Отключения',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/technicalControl/weathersPredbill',
        'name': 'Ввод данных с метеостанций',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/technicalControl/modeCardsPredBill',
        'name': 'Режимные карты',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integrations/asupr/statementUploadLog',
        'name': 'АСУПР:Журнал получения ведомостей',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integrations/asupr/directoryReceiptLog',
        'name': 'АСУПР:Журнал получения справочников',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integrations/asupr/comparisonLog',
        'name': 'АСУПР:Журнал сопоставления справочников',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integrations/elk/statementUploadLog',
        'name': 'ЕЛК: Журнал получения ведомостей',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integrations/elk/watermeterStatementUploadLogElk',
        'name': 'ЕЛК: Получение данных из файла по ВПУ',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integration/asot/informationJournal',
        'name': 'АСОТ: Журнал получения данных',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integration/esm/log',
        'name': 'ЕСМ: Журнал взаимодействия',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integration/mvk/log',
        'name': 'МВК: Журнал взаимодействия',
        'check_filters': True,
        'table_type': 'default'
    },
{
        'url': 'http://10.5.121.74/integrations/assdPsd/statementUploadLog',
        'name': 'АССД ПСД: Журнал получения ведомостей',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integration/eksnsi/log',
        'name': 'ЕКС НСИ: Журнал обмена данными',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integration/komm/logs',
        'name': 'ИС СБЫТ: Журнал обмена данными- Общая статистика',
        'check_filters': False,
        'table_type': 'komm_tables'
    },
    {
        'url': 'http://10.5.121.74/integration/komm/errors',
        'name': 'ИС СБЫТ: Журнал обмена данными- Журнал ошибок',
        'check_filters': False,
        'table_type': 'komm_tables'
    },
    {
        'url': 'http://10.5.121.74/integrations/application',
        'name': 'Заявки в УКУиКЭ',
        'check_filters': False,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/analytics/analyticReportsPredBill',
        'name': 'Аналитика и отчетность',
        'check_filters': False,
        'table_type': 'analytics_tables'
    },
    {
        'url': 'http://10.5.121.74/catalog',
        'name': 'Нормативно-справочная информация',
        'check_filters': False,
        'table_type': 'catalog_tables'
    },
    {
        'url': 'http://10.5.121.74/administration/roles',
        'name': 'Администрирование:Роли',
        'check_filters': False,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/administration/systemUsers',
        'name': 'Администрирование:Пользователи',
        'check_filters': False,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/administration/uiElements',
        'name': 'Администрирование:Элементы интерфейса',
        'check_filters': False,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/administration/cronRegistry',
        'name': 'Администрирование:Планировщик',
        'check_filters': False,
        'table_type': 'default'
    },
]

# Проверяем все разделы
for section in sections:
    check_filters = section.get('check_filters', True)
    table_type = section.get('table_type', 'default')

    errors = test_section(section['url'], section['name'], check_filters, table_type)

    # Сохраняем результаты
    all_results[section['name']] = {
        'errors': errors,
        'error_count': len(errors),
        'url': section['url'],
        'check_filters': check_filters,
        'table_type': table_type,
        'timestamp': time.strftime('%H:%M:%S')
    }

# Финальный отчет
print_header("ФИНАЛЬНЫЙ ОТЧЕТ")

total_sections = len(all_results)
sections_with_errors = sum(1 for result in all_results.values() if result['error_count'] > 0)
sections_ok = total_sections - sections_with_errors

print(f"\nОБЩАЯ СТАТИСТИКА:")
print(f"{'─' * 40}")
print(f"   • Всего проверено разделов: {total_sections}")
print(f"   • Без ошибок: {sections_ok}")
print(f"   • С ошибками: {sections_with_errors}")
# Считаем уникальные ошибки по всему тесту (раздел + текст ошибки)
all_unique_errors_set = set()
for section_name, result in all_results.items():
    if result['error_count'] > 0:
        for error in result['errors']:
            # Добавляем ошибку с указанием раздела, чтобы ошибки из разных разделов считались уникальными
            all_unique_errors_set.add(f"{section_name}: {error}")

print(f"   • Всего уникальных ошибок: {len(all_unique_errors_set)}")

# Статистика по времени загрузки
if load_times:
    # Используем load_duration (время загрузки после сброса фильтров)
    load_durations = [info.get('load_duration', 0) for info in load_times.values() if info.get('load_duration', 0) > 0]

    if load_durations:
        total_duration = sum(load_durations)
        avg_duration = total_duration / len(load_durations)
        max_duration = max(load_durations)

        # Находим раздел с максимальным временем загрузки
        max_section = None
        for section_name, info in load_times.items():
            if info.get('load_duration', 0) == max_duration:
                max_section = section_name
                break

        print(f"\nСТАТИСТИКА ВРЕМЕНИ ЗАГРУЗКИ (после сброса фильтров):")
        print(f"{'─' * 40}")
        print(f"   • Общее время загрузки: {total_duration:.1f} сек")
        #print(f"   • Среднее время на раздел: {avg_duration:.1f} сек")
        print(f"   • Самый долгий раздел: {max_section} ({max_duration:.1f} сек)")

        # Выводим 5 самых долгих разделов
        print(f"\n   5 самых долгих разделов:")
        sorted_times = sorted(load_times.items(), key=lambda x: x[1].get('load_duration', 0), reverse=True)[:5]
        for i, (section, info) in enumerate(sorted_times, 1):
            duration = info.get('load_duration', 0)
            if duration > 0:
                print(f"      {i}. {section}: {duration:.1f} сек")

print(f"\nРЕЗУЛЬТАТЫ ПО РАЗДЕЛАМ:")
print(f"{'─' * 60}")

for section_name, result in all_results.items():
    # Получаем время загрузки для этого раздела
    load_info = load_times.get(section_name, {})
    duration = load_info.get('load_duration', 0)

    if result['error_count'] == 0:
        if duration > 0:
            print(f"   УСПЕХ {section_name} [{duration:.1f} сек]")
        else:
            print(f"   УСПЕХ {section_name}")
    else:
        # Берем только уникальные ошибки в разделе (без дублей по тексту)
        unique_errors = list(set(result['errors']))
        if duration > 0:
            print(f"   ОШИБКА {section_name} - {len(unique_errors)} ошиб. [{duration:.1f} сек]")
        else:
            print(f"   ОШИБКА {section_name} - {len(unique_errors)} ошиб.")

print(f"\nСПИСОК ОШИБОК ПО РАЗДЕЛАМ:")
print(f"{'─' * 80}")

# Собираем разделы с ошибками
sections_with_errors_list = []
for section_name, result in all_results.items():
    if result['error_count'] > 0:
        sections_with_errors_list.append(section_name)

# Выводим ошибки по каждому разделу отдельно
for section_name in sections_with_errors_list:
    result = all_results[section_name]
    print(f"\nОШИБКИ В РАЗДЕЛЕ {section_name}:")
    print(f"   {'─' * 40}")

    # Берем только уникальные ошибки в разделе (без дублей по тексту)
    unique_errors = []
    seen_errors = set()
    for error in result['errors']:
        if error not in seen_errors:
            seen_errors.add(error)
            unique_errors.append(error)

    if unique_errors:
        for i, error in enumerate(unique_errors, 1):
            # Разбиваем ошибку на строки если она многострочная
            error_lines = error.split('\n')
            if len(error_lines) > 1:
                print(f"   {i}. {error_lines[0]}")
                for line in error_lines[1:]:
                    if line.strip():  # Пропускаем пустые строки
                        print(f"     {line}")
            else:
                print(f"   {i}. {error}")

print(f"\n{'═' * 50}")

# Итоговый вывод
if len(sections_with_errors_list) == 0:
    print(f"ВСЕ РАЗДЕЛЫ РАБОТАЮТ КОРРЕКТНО!")
    print(f"Система готова к использованию")
else:
    # Считаем общее количество уникальных ошибок
    total_unique_errors = 0
    for section_name in sections_with_errors_list:
        result = all_results[section_name]
        unique_errors_set = set(result['errors'])  # Уникальные ошибки в разделе
        total_unique_errors += len(unique_errors_set)

    print(f"ВСЕГО ОШИБОК: {total_unique_errors}")
    print(f"Требуется исправление")

print(f"{'=' * 80}")

# Подсчет общего времени выполнения скрипта
total_script_end_time = time.time()
total_script_duration = total_script_end_time - total_script_start_time

minutes = int(total_script_duration // 60)
seconds = total_script_duration % 60

print(f"\n{'=' * 60}")
print(f"ОБЩЕЕ ВРЕМЯ ВЫПОЛНЕНИЯ СКРИПТА: {minutes} мин {seconds:.1f} сек")
print(f"{'=' * 60}")

# Закрытие браузера
try:
    print("\nЗакрытие браузера...")
    driver.quit()
    print("Браузер успешно закрыт")
except Exception as e:
    print(f"Не удалось закрыть браузер: {e}")