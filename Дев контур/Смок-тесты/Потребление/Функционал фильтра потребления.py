"""
ТЕСТ: Проверка функциональности фильтра в разделе "Точки учета (Потребление)"

Что тестирует:
1. Авторизация в системе
2. Переход в раздел "Точки учета (Потребление)"
3. Проверка наличия ошибок на странице
4. Открытие фильтра и сброс перед заполнением
5. Последовательное заполнение ВСЕХ полей фильтра случайными значениями
6. Сброс фильтров и проверка очистки всех полей (с учетом плейсхолдеров)
7. Выбор случайного АО и проверка фильтрации данных в таблице
8. Финальный сброс фильтров и генерация отчета
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import re

# Инициализация драйвера
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()
wait = WebDriverWait(driver, 60)

# Данные для авторизации
from config import USERNAME, PASSWORD
URL = 'http://10.5.121.74/login'

# ============================================
# СЕЛЕКТОРЫ
# ============================================

# Основные селекторы
FILTER_SELECTOR = "svg[data-icon='filter']"
APPLY_BUTTON_SELECTOR = "div.filterOperations > button:nth-child(1)"
RESET_BUTTON_SELECTOR = "div.filterOperations > button:nth-child(2)"
TABLE_SELECTOR = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body"

# Запасные селекторы для кнопок
APPLY_SVG_FALLBACK = "svg[data-icon='check']"
RESET_SVG_FALLBACK = "svg[data-icon='stop']"

# Селекторы для проверки ошибок
ERROR_SELECTORS = [
    "div.ant-notification-notice-error",
    "div.ant-alert-error",
    ".ant-message-error"
]

# Селекторы для закрытия ошибок
CLOSE_SELECTORS = [
    "span.ant-notification-notice-close-x",
    ".ant-notification-notice-close",
    ".ant-alert-close-icon",
    ".ant-message-notice-close",
    "[aria-label='close']",
    ".anticon-close"
]

# Селекторы для ожидания загрузки
LOADING_SELECTORS = [
    "div.ant-spin.ant-spin-spinning",
    "div.ant-spin-spinning",
    "span.anticon-loading.anticon-spin"
]

# ============================================
# СПИСОК ПОЛЕЙ ДЛЯ ЗАПОЛНЕНИЯ
# ============================================

FIELD_CONFIGS = [
    # Основные поля
    {"label": "Данные за РП", "type": "multiselect_random", "id": "actualCommercialReportState"},
    {"label": "Объем подпитки", "type": "single_select_random", "id": "checkVolumeMeasure"},
    {"label": "Тип ТУ", "type": "multiselect_random", "id": "typeCode"},
    {"label": "Статус ТУ", "type": "multiselect_random", "id": "status"},
    {"label": "Эксплуатация", "type": "multiselect_random", "id": "exploitationStatus"},
    {"label": "Потребитель", "type": "input", "id": "consumerName", "value": "Тестовый потребитель"},
    {"label": "Договор", "type": "input", "id": "serviceAgreementsNumber", "value": "123/45"},

    # Расположение
    {"label": "АО", "type": "multiselect_random", "id": "aoDistrictCode", "save_for_check": True},
    {"label": "Район", "type": "multiselect_random", "id": "rayonCode"},
    {"label": "Адрес", "type": "address", "id": "fullAddressIds"},
    {"label": "Филиал", "type": "multiselect_random", "id": "filialCode"},
    {"label": "Предприятие", "type": "multiselect_random", "id": "predpriyatieCode", "depends_on": "filialCode"},
    {"label": "Номер ТП", "type": "input", "id": "heatPointNumber", "value": "123"},
    {"label": "Тип объекта", "type": "multiselect_random", "id": "heatPointType"},

    # Приборы
    {"label": "Тип ПУ", "type": "multiselect_random", "id": "meteringDeviceConstructType"},
    {"label": "Вид ПУ", "type": "single_select_random", "id": "kindMd"},
    {"label": "Марка ПУ", "type": "multiselect_random", "id": "meteringDeviceModelId"},
    {"label": "Номер ПУ", "type": "input", "id": "meteringDeviceSeries", "value": "158"},
    {"label": "БП", "type": "multiselect_random", "id": "deviceBalanceConsumerId"},
    {"label": "Прибор МВК", "type": "single_select_random", "id": "signMvk"},
    {"label": "Виртуальный", "type": "single_select_random", "id": "signVirtual"},
    {"label": "Сальдирующий", "type": "single_select_random", "id": "signSaldo"},
    {"label": "Параллельные ПУ", "type": "single_select_random", "id": "hasParallelDevices"}
]

# Поля, после которых НЕ нужно нажимать Tab
NO_TAB_FIELDS = ["Район", "Адрес"]

# ============================================
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# ============================================

error_log = {
    "total_errors_found": 0,
    "errors_closed": 0,
    "errors_details": []
}

current_action_context = "Начало теста"
results = {}
selected_ao_value = None
skipped_fields = []


# ============================================
# ФУНКЦИИ ДЛЯ УМНОГО ОЖИДАНИЯ И ЗАКРЫТИЯ ОШИБОК
# ============================================

def try_close_error():
    """Пытается закрыть ошибку по крестику"""
    try:
        for selector in CLOSE_SELECTORS:
            try:
                close_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in close_buttons:
                    try:
                        if btn.is_displayed() or btn.is_enabled():
                            try:
                                btn.click()
                            except:
                                driver.execute_script("arguments[0].click();", btn)
                            print(f"  Найден и кликнут крестик")
                            error_log["errors_closed"] += 1
                            time.sleep(0.2)
                            return True
                    except:
                        try:
                            driver.execute_script("arguments[0].click();", btn)
                            print(f"  Кликнут крестик через JS")
                            error_log["errors_closed"] += 1
                            time.sleep(0.2)
                            return True
                        except:
                            continue
            except:
                continue
        return False
    except Exception as e:
        print(f"  Ошибка при попытке закрыть ошибку: {e}")
        return False


def check_for_persistent_errors():
    """Проверяет наличие стойких ошибок"""
    global current_action_context

    for selector in ERROR_SELECTORS:
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
                                    "успешно" not in text_lower):
                                error_log["total_errors_found"] += 1
                                error_log["errors_details"].append({
                                    "time": time.strftime("%H:%M:%S"),
                                    "context": current_action_context,
                                    "text": error_text[:200]
                                })
                                return True
                except:
                    continue
        except:
            continue
    return False


def smart_wait_for_errors_disappear():
    """Умное ожидание исчезновения ошибок"""
    print(f"\nУмное ожидание исчезновения ошибок...")
    start_wait_time = time.time()
    max_wait_time = 5

    try:
        while time.time() - start_wait_time < max_wait_time:
            if check_for_persistent_errors():
                elapsed = time.time() - start_wait_time
                if elapsed > 0.5:
                    print(f"  Ошибка держится {elapsed:.1f}с, пробуем закрыть...")
                    try_close_error()
                time.sleep(0.5)
            else:
                return True
        return False
    except Exception as e:
        print(f"Исключение в умном ожидании: {e}")
        return False


def wait_for_page_load(context=""):
    """Ожидание загрузки данных"""
    global current_action_context
    if context:
        current_action_context = f"Загрузка страницы: {context}"

    print("Ожидание загрузки данных...")
    load_start = time.time()

    try:
        for selector in LOADING_SELECTORS:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        if element.is_displayed():
                            wait.until(EC.invisibility_of_element(element))
                    except:
                        continue
            except:
                continue

        load_duration = time.time() - load_start
        print(f"Загрузка данных завершена за {load_duration:.1f} секунд")
        smart_wait_for_errors_disappear()
        return load_duration

    except Exception as e:
        print(f"  Ошибка при ожидании загрузки: {e}")
        smart_wait_for_errors_disappear()
        return time.time() - load_start


def add_error(error_text):
    """Добавляет ошибку"""
    error_log["errors_details"].append({
        "time": time.strftime("%H:%M:%S"),
        "context": current_action_context,
        "text": error_text
    })
    print(f"ОШИБКА: {error_text}")


def add_skipped_field(field_name, reason):
    """Добавляет пропущенное поле"""
    skipped_fields.append({"field": field_name, "reason": reason})
    print(f"Пропущено поле '{field_name}': {reason}")


def click_svg_element(svg_selector, action_name, context=""):
    """Клик по SVG элементу"""
    global current_action_context
    if context:
        current_action_context = context

    try:
        svg_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, svg_selector))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", svg_element)
        time.sleep(0.3)

        try:
            parent_button = svg_element.find_element(By.XPATH, "..")
            parent_button.click()
            print(f"✓ {action_name}")
            time.sleep(0.5)
            return True
        except:
            svg_element.click()
            print(f"✓ {action_name}")
            time.sleep(0.5)
            return True
    except Exception as e:
        print(f"✗ Не удалось {action_name}: {e}")
        return False


def press_tab():
    """Нажимает Tab"""
    try:
        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB).perform()
        time.sleep(0.3)
        return True
    except:
        return False


# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЯМИ
# ============================================

def find_field_by_id(field_id):
    """Находит поле по ID"""
    try:
        element = driver.find_element(By.ID, field_id)
        return element
    except:
        return None


def find_field_by_label(label_text):
    """Находит поле по тексту лейбла"""
    try:
        label_xpath = f"//label[contains(text(), '{label_text}')]"
        label = driver.find_element(By.XPATH, label_xpath)
        row = label.find_element(By.XPATH, "./ancestor::div[contains(@class, 'ant-row')]")
        return row
    except:
        return None


def process_multiselect_random(field_config):
    """Обрабатывает мультиселект с случайным выбором"""
    field_name = field_config["label"]
    field_id = field_config.get("id")

    try:
        print(f"\nОбрабатываем поле: {field_name}")

        # Пробуем найти по ID
        if field_id:
            field_element = driver.find_element(By.ID, field_id)
        else:
            row = find_field_by_label(field_name)
            if not row:
                add_skipped_field(field_name, "Поле не найдено")
                return False
            field_element = row.find_element(By.CSS_SELECTOR, "input.ant-select-selection-search-input")

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field_element)
        time.sleep(0.3)

        # Кликаем на родительский селектор
        parent_selector = field_element.find_element(By.XPATH,
                                                     "./ancestor::div[contains(@class, 'ant-select-selector')]")
        parent_selector.click()
        print(f"  Открыли выпадающий список")
        time.sleep(1)

        # Ждем появления списка
        dropdown = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ant-select-dropdown:not(.ant-select-dropdown-hidden)"))
        )

        # Ищем опции
        options = dropdown.find_elements(By.CSS_SELECTOR, ".ant-select-item-option")
        print(f"  Найдено опций: {len(options)}")

        if not options:
            add_skipped_field(field_name, "Список пуст")
            return False

        # Фильтруем опции (исключаем "Выбрать все")
        valid_options = []
        for option in options:
            try:
                option_text = option.text.strip()
                if "Выбрать все" not in option_text and option_text:
                    valid_options.append(option)
            except:
                continue

        if not valid_options:
            add_skipped_field(field_name, "Нет доступных значений")
            return False

        # Выбираем случайное значение
        random_option = random.choice(valid_options)
        option_text = random_option.text.strip()
        random_option.click()
        print(f"  Выбрано: '{option_text}'")

        # Сохраняем значение АО для проверки
        if field_config.get("save_for_check"):
            global selected_ao_value
            selected_ao_value = option_text

        time.sleep(0.5)
        smart_wait_for_errors_disappear()
        return True

    except Exception as e:
        print(f"  Ошибка: {e}")
        add_skipped_field(field_name, str(e)[:100])
        return False


def process_single_select_random(field_config):
    """Обрабатывает одиночный селект с случайным выбором"""
    field_name = field_config["label"]
    field_id = field_config.get("id")

    try:
        print(f"\nОбрабатываем поле: {field_name}")

        # Пробуем найти по ID
        if field_id:
            field_element = driver.find_element(By.ID, field_id)
        else:
            row = find_field_by_label(field_name)
            if not row:
                add_skipped_field(field_name, "Поле не найдено")
                return False
            field_element = row.find_element(By.CSS_SELECTOR, "input.ant-select-selection-search-input")

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field_element)
        time.sleep(0.3)

        # Кликаем на родительский селектор
        parent_selector = field_element.find_element(By.XPATH,
                                                     "./ancestor::div[contains(@class, 'ant-select-selector')]")
        parent_selector.click()
        print(f"  Открыли выпадающий список")
        time.sleep(1)

        # Ждем появления списка
        dropdown = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ant-select-dropdown:not(.ant-select-dropdown-hidden)"))
        )

        # Ищем опции
        options = dropdown.find_elements(By.CSS_SELECTOR, ".ant-select-item-option")
        print(f"  Найдено опций: {len(options)}")

        if not options:
            add_skipped_field(field_name, "Список пуст")
            return False

        # Для одиночного селекта берем любую опцию
        valid_options = [o for o in options if o.text.strip()]

        if not valid_options:
            add_skipped_field(field_name, "Нет доступных значений")
            return False

        # Выбираем случайное значение
        random_option = random.choice(valid_options)
        option_text = random_option.text.strip()
        random_option.click()
        print(f"  Выбрано: '{option_text}'")

        time.sleep(0.5)
        smart_wait_for_errors_disappear()
        return True

    except Exception as e:
        print(f"  Ошибка: {e}")
        add_skipped_field(field_name, str(e)[:100])
        return False


def process_input_field(field_config):
    """Обрабатывает текстовое поле"""
    field_name = field_config["label"]
    field_id = field_config.get("id")
    value = field_config.get("value", "Тестовое значение")

    try:
        print(f"\nОбрабатываем поле: {field_name}")

        # Пробуем найти по ID
        if field_id:
            field_element = driver.find_element(By.ID, field_id)
        else:
            row = find_field_by_label(field_name)
            if not row:
                add_skipped_field(field_name, "Поле не найдено")
                return False
            field_element = row.find_element(By.CSS_SELECTOR, "input")

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field_element)
        time.sleep(0.3)

        field_element.click()
        time.sleep(0.3)
        field_element.clear()
        time.sleep(0.3)
        field_element.send_keys(value)
        print(f"  Введено: '{value}'")

        time.sleep(0.5)
        smart_wait_for_errors_disappear()
        return True

    except Exception as e:
        print(f"  Ошибка: {e}")
        add_skipped_field(field_name, str(e)[:100])
        return False


def process_address_field(field_config):
    """Обрабатывает поле адреса"""
    field_name = field_config["label"]
    address_value = "1-й Амбулаторный пр., д.2/6"

    try:
        print(f"\nОбрабатываем поле: {field_name}")

        # Находим по лейблу
        row = find_field_by_label(field_name)
        if not row:
            add_skipped_field(field_name, "Поле не найдено")
            return False

        address_field = row.find_element(By.CSS_SELECTOR, ".searchableSelectHeader")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", address_field)
        time.sleep(0.3)
        address_field.click()
        print(f"  Кликнули на поле адреса")
        time.sleep(2)

        # Ждем появления окна поиска
        popup = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".searchableSelectPopup"))
        )

        # Находим поле ввода
        search_input = popup.find_element(By.CSS_SELECTOR, "input.searchInput")
        search_input.clear()
        search_input.send_keys(address_value)
        print(f"  Ввели адрес: {address_value}")
        time.sleep(3)

        # Ждем появления списка
        items_list = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".itemsList"))
        )
        items = items_list.find_elements(By.TAG_NAME, "li")

        if items:
            # Выбираем первый элемент
            items[0].click()
            print(f"  Выбрали адрес из списка")
            time.sleep(1)

            # Кликаем на поле "Данные за РП" чтобы закрыть список
            try:
                first_field = driver.find_element(By.ID, "actualCommercialReportState")
                first_field.click()
            except:
                actions = ActionChains(driver)
                actions.move_by_offset(100, 100).click().perform()

            time.sleep(0.5)
            smart_wait_for_errors_disappear()
            return True
        else:
            add_skipped_field(field_name, "Список адресов пуст")
            return False

    except Exception as e:
        print(f"  Ошибка: {e}")
        add_skipped_field(field_name, str(e)[:100])
        return False


def check_field_emptiness(field_config):
    """Проверяет, что поле пустое после сброса"""
    field_name = field_config["label"]
    field_id = field_config.get("id")
    field_type = field_config["type"]

    placeholder_texts = [
        "Выберите значение", "Select value", "Введите значение",
        "Введите серийный номер", "Выбрать", "Choose"
    ]

    try:
        if field_type == "address":
            # Для адреса проверяем текст
            row = find_field_by_label(field_name)
            if row:
                address_field = row.find_element(By.CSS_SELECTOR, ".searchableSelectHeader")
                field_text = address_field.text.strip()
                is_placeholder = any(ph in field_text for ph in placeholder_texts) or field_text == ""
                if field_text and not is_placeholder:
                    return False, f"{field_name}: {field_text}"

        elif field_type in ["multiselect_random", "single_select_random"]:
            # Для селектов
            if field_id:
                field_element = driver.find_element(By.ID, field_id)
                field_text = field_element.get_attribute("value") or ""
                if field_text:
                    return False, f"{field_name}: {field_text}"
            else:
                row = find_field_by_label(field_name)
                if row:
                    selector = row.find_element(By.CSS_SELECTOR, ".ant-select-selector")
                    field_text = selector.text.strip()
                    is_placeholder = any(ph in field_text for ph in placeholder_texts)
                    if field_text and not is_placeholder:
                        return False, f"{field_name}: {field_text}"

        elif field_type == "input":
            # Для текстовых полей
            if field_id:
                field_element = driver.find_element(By.ID, field_id)
                field_value = field_element.get_attribute("value")
                if field_value:
                    return False, f"{field_name}: {field_value}"

        return True, None

    except Exception as e:
        print(f"  {field_name}: ошибка проверки - {str(e)[:50]}")
        return True, None


def check_all_fields_empty():
    """Проверяет, что все поля пустые после сброса"""
    print("\nПроверяем сброс всех полей фильтра...")
    not_emptied = []

    for config in FIELD_CONFIGS:
        is_empty, error_info = check_field_emptiness(config)
        if not is_empty and error_info:
            not_emptied.append(error_info)
            print(f"  {error_info}")

    return not_emptied


def apply_filter():
    """Применяет фильтр"""
    try:
        print("\nПрименяем фильтр...")
        try:
            # Пробуем найти кнопку по селектору
            apply_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, APPLY_BUTTON_SELECTOR))
            )
            apply_button.click()
            print("✓ Фильтр применен")
        except:
            # Запасной вариант - ищем по иконке
            apply_svg = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, APPLY_SVG_FALLBACK))
            )
            parent_button = apply_svg.find_element(By.XPATH, "..")
            parent_button.click()
            print("✓ Фильтр применен (по иконке)")

        time.sleep(2)
        wait_for_page_load("после применения фильтра")
        return True
    except Exception as e:
        print(f"✗ Не удалось применить фильтр: {e}")
        return False


def reset_filter():
    """Сбрасывает фильтр"""
    try:
        print("\nСбрасываем фильтр...")
        try:
            # Пробуем найти кнопку по селектору
            reset_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, RESET_BUTTON_SELECTOR))
            )
            reset_button.click()
            print("✓ Фильтр сброшен")
        except:
            # Запасной вариант - ищем по иконке
            reset_svg = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, RESET_SVG_FALLBACK))
            )
            parent_button = reset_svg.find_element(By.XPATH, "..")
            parent_button.click()
            print("✓ Фильтр сброшен (по иконке)")

        time.sleep(1)
        wait_for_page_load("после сброса фильтра")
        return True
    except Exception as e:
        print(f"✗ Не удалось сбросить фильтр: {e}")
        return False


def check_table_for_ao(selected_ao):
    """Проверяет таблицу на соответствие выбранному АО"""
    try:
        print(f"\nПроверяем таблицу для АО: '{selected_ao}'")
        wait_for_page_load("перед проверкой таблицы")

        table_body = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, TABLE_SELECTOR))
        )

        rows = table_body.find_elements(By.CSS_SELECTOR, ".BaseTable__row")

        if not rows:
            add_error(f"Таблица пуста после применения фильтра с АО: '{selected_ao}'")
            return False, 0

        print(f"  Найдено строк: {len(rows)}")

        # Проверяем наличие АО в строках
        mismatched = []
        for i, row in enumerate(rows, 1):
            row_text = row.text
            if selected_ao not in row_text:
                mismatched.append(i)
                if len(mismatched) <= 3:
                    print(f"    Строка {i}: НЕ содержит '{selected_ao}'")

        if mismatched:
            add_error(f"Найдены строки не соответствующие АО '{selected_ao}': {mismatched[:5]}")
            return False, len(rows)

        print(f"  Все строки соответствуют АО: '{selected_ao}'")
        return True, len(rows)

    except Exception as e:
        add_error(f"Ошибка при проверке таблицы: {e}")
        return False, 0


# ============================================
# ОСНОВНОЙ СКРИПТ
# ============================================

print("=" * 60)
print("ТЕСТ ФИЛЬТРАЦИИ: Точки учета (Потребление)")
print("=" * 60)

# 1. АВТОРИЗАЦИЯ
print("\n" + "=" * 50)
print("ШАГ 1: АВТОРИЗАЦИЯ")
print("=" * 50)

try:
    current_action_context = "Авторизация"
    driver.get(URL)
    username_field = wait.until(EC.presence_of_element_located((By.ID, "normal_login_username")))
    username_field.send_keys(USERNAME)
    password_field = driver.find_element(By.ID, "normal_login_password")
    password_field.send_keys(PASSWORD)
    login_button = driver.find_element(By.CSS_SELECTOR, '.ant-btn.ant-btn-primary.w-100.mb-s')
    login_button.click()
    wait.until_not(EC.url_contains('login'))
    print("✓ Авторизация успешна")
    smart_wait_for_errors_disappear()
except Exception as e:
    print(f"✗ Авторизация не удалась: {e}")
    driver.quit()
    exit()

# 2. ПЕРЕХОД В РАЗДЕЛ
print("\n" + "=" * 50)
print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ 'ТОЧКИ УЧЕТА (ПОТРЕБЛЕНИЕ)'")
print("=" * 50)

try:
    current_action_context = "Переход в раздел"
    section_url = 'http://10.5.121.74/technicalControl/meteringPointsPredBill'
    driver.get(section_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print(f"✓ Переход в раздел")
    time.sleep(2)
    smart_wait_for_errors_disappear()
    wait_for_page_load("после перехода")
except Exception as e:
    print(f"✗ Не удалось перейти в раздел: {e}")
    driver.quit()
    exit()

# 3. ПРОВЕРКА ОШИБОК НА СТРАНИЦЕ
print("\n" + "=" * 50)
print("ШАГ 3: ПРОВЕРКА ОШИБОК НА СТРАНИЦЕ")
print("=" * 50)

smart_wait_for_errors_disappear()

# 4. ОТКРЫТИЕ ФИЛЬТРА
print("\n" + "=" * 50)
print("ШАГ 4: ОТКРЫТИЕ ФИЛЬТРА")
print("=" * 50)

if click_svg_element(FILTER_SELECTOR, "Открыть фильтр", "Открытие фильтра"):
    print("✓ Фильтр открыт")
    time.sleep(2)
else:
    add_error("Не удалось открыть фильтр")
    driver.quit()
    exit()

# 5. СБРОС ФИЛЬТРОВ ПЕРЕД ЗАПОЛНЕНИЕМ
print("\n" + "=" * 50)
print("ШАГ 5: СБРОС ФИЛЬТРОВ ПЕРЕД ЗАПОЛНЕНИЕМ")
print("=" * 50)

reset_filter()

# 6. ЗАПОЛНЕНИЕ ПОЛЕЙ ФИЛЬТРА
print("\n" + "=" * 50)
print("ШАГ 6: ЗАПОЛНЕНИЕ ПОЛЕЙ ФИЛЬТРА")
print("=" * 50)

for i, config in enumerate(FIELD_CONFIGS, 1):
    field_name = config["label"]
    field_type = config["type"]

    print(f"\n[{i}/{len(FIELD_CONFIGS)}] {field_name}")

    if field_type == "multiselect_random":
        success = process_multiselect_random(config)
    elif field_type == "single_select_random":
        success = process_single_select_random(config)
    elif field_type == "input":
        success = process_input_field(config)
    elif field_type == "address":
        success = process_address_field(config)
    else:
        success = False

    results[field_name] = success

    # Нажимаем Tab после каждого поля, кроме:
    # 1. Последнего поля
    # 2. Полей из списка NO_TAB_FIELDS
    if i < len(FIELD_CONFIGS) and field_name not in NO_TAB_FIELDS:
        press_tab()
        time.sleep(0.3)
    elif field_name in NO_TAB_FIELDS and i < len(FIELD_CONFIGS):
        print(f"  ⏭ Пропускаем Tab после поля '{field_name}'")

print("\n✓ Все поля обработаны")

# 7. СБРОС ФИЛЬТРОВ И ПРОВЕРКА ОЧИСТКИ
print("\n" + "=" * 50)
print("ШАГ 7: СБРОС ФИЛЬТРОВ И ПРОВЕРКА ОЧИСТКИ")
print("=" * 50)

reset_filter()

# Проверяем, что все поля сбросились
not_emptied = check_all_fields_empty()

if not_emptied:
    print(f"\n⚠ Найдены поля, которые не сбросились ({len(not_emptied)}):")
    for field_info in not_emptied:
        add_error(f"Поле не сбросилось: {field_info}")
else:
    print("\n✓ Все поля успешно сброшены!")

# 8. ВЫБОР И ПРОВЕРКА АО
print("\n" + "=" * 50)
print("ШАГ 8: ВЫБОР И ПРОВЕРКА АО")
print("=" * 50)

# Находим конфиг для АО
ao_config = next((c for c in FIELD_CONFIGS if c["label"] == "АО"), None)

if ao_config:
    if process_multiselect_random(ao_config):
        if selected_ao_value:
            print(f"\nВыбрано АО для проверки: '{selected_ao_value}'")

            if apply_filter():
                table_valid, row_count = check_table_for_ao(selected_ao_value)

                if table_valid:
                    print(f"\n✓ Таблица проверена успешно!")
                else:
                    print(f"\n✗ Ошибка при проверке таблицы")
        else:
            add_error("Не удалось сохранить значение АО")
    else:
        add_error("Не удалось выбрать АО")
else:
    add_error("Конфиг для АО не найден")





# 10. ИТОГОВЫЙ ОТЧЕТ
print("\n" + "=" * 80)
print("ИТОГОВЫЙ ОТЧЕТ")
print("=" * 80)

print(f"\nРЕЗУЛЬТАТЫ ОБРАБОТКИ ПОЛЕЙ:")
for field_name, status in results.items():
    print(f"  {'✓' if status else '✗'} {field_name}")

if skipped_fields:
    print(f"\nПРОПУЩЕННЫЕ ПОЛЯ ({len(skipped_fields)}):")
    for skipped in skipped_fields:
        print(f"  • {skipped['field']}: {skipped['reason']}")

print(f"\nПРОВЕРКА ФИЛЬТРАЦИИ ПО АО:")
if selected_ao_value:
    print(f"  Выбранное АО: '{selected_ao_value}'")
    if 'table_valid' in locals():
        if table_valid:
            print(f"  Статус: УСПЕШНО")
            print(f"  Количество строк: {row_count}")
        else:
            print(f"  Статус: ПРОВАЛЕН")
    else:
        print(f"  Статус: ПРОВЕРКА НЕ ВЫПОЛНЕНА")

print(f"\nИНФОРМАЦИЯ ОБ ОШИБКАХ:")
print(f"  • Всего ошибок найдено: {error_log['total_errors_found']}")
print(f"  • Успешно закрыто: {error_log['errors_closed']}")

if error_log['errors_details']:
    print(f"  • Детали ошибок:")
    for i, err in enumerate(error_log['errors_details'], 1):
        print(f"    {i}. [{err['time']}] {err['context']}")
        print(f"       {err['text']}")

print(f"\nОБЩИЙ ИТОГ:")
test_passed = (len(skipped_fields) == 0 and
               error_log['total_errors_found'] == 0 and
               'table_valid' in locals() and table_valid)
print(f"  {'✓ ПРОЙДЕН' if test_passed else '✗ НЕ ПРОЙДЕН'}")

print("=" * 80)

# Закрытие браузера
try:
    print("\nЗакрытие браузера...")
    time.sleep(2)
    driver.quit()
    print("✓ Браузер успешно закрыт")
except Exception as e:
    print(f"✗ Не удалось закрыть браузер: {e}")