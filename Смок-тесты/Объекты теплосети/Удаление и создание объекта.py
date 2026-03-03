"""
ТЕСТ: Создание объекта теплосети после удаления существующего

Что тестирует:
1. Авторизация в системе
2. Переход в раздел "Объекты теплосети"
3. Выбор случайного объекта и его удаление
4. Создание нового объекта с тем же адресом
5. Для КАЖДОГО из трех типов (Тепловой пункт, Присоединенное строение, Источник теплоснабжения):
   - Выбор типа по индексу (1, 2, 3)
   - Ввод адреса (только для первого типа, потом адрес сохраняется)
   - Получение строк таблицы
   - Клик по каждой строке (с ожиданием 1 сек)
   - Проверка, что адрес в строке совпадает с введенным
   - Проверка активности кнопки "Сохранить"
6. Если на каком-то типе кнопка стала активной и адрес совпадает - сохраняем объект
7. Если после всех трех типов кнопка так и не стала активной - выводим ошибку
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
RESET_SELECTOR = "svg[data-icon='stop']"
APPLY_SELECTOR = "svg[data-icon='check']"

# Селекторы для работы с объектами
CHECKBOX_SELECTOR_TEMPLATE = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body > div > div:nth-child({}) > div:nth-child(1) > label"

# Селектор для меню действия (как в экспорте объектов)
ACTION_MENU_SELECTOR = "#root > section > section > div > div.ant-space.ant-space-horizontal.ant-space-align-center > div > div > div > div > div > button > div > div:nth-child(1) > span > svg"

# Селекторы для пунктов меню
DELETE_MENU_ITEM_SELECTOR = "html > div > div > div > ul > li:nth-child(3) > span > button"  # Удалить
CREATE_MENU_ITEM_SELECTOR = "html > div > div > div > ul > li:nth-child(1) > span > button"  # Создать

# Селекторы модального окна удаления
DELETE_MODAL_ADDRESS = "#deleteModalForm_fullAddress"
DELETE_BUTTON = "#deleteModalForm > div.rt-form-footer > button.ant-btn.ant-btn-primary.ml-s"

# Селекторы модального окна создания
TYPE_FIELD = "#saveAccountingObjectModalForm > div.rt-form-body > div:nth-child(2) > div.ant-col.ant-col-16.ant-form-item-control > div > div > div"  # Поле типа
TYPE_DROPDOWN = ".ant-select-dropdown"  # Выпадающий список
TYPE_OPTION = ".ant-select-item-option"  # Опция в списке
ADDRESS_INPUT = "#saveAccountingObjectModalForm_address"  # Поле ввода адреса
TABLE_ROWS = "#saveAccountingObjectModalForm > div.rt-form-body > div.rt-table.addAccountingTable .BaseTable__row"  # Строки таблицы
TABLE_CELL_ADDRESS = "div.BaseTable__row-cell:nth-child(1) .textEllipsis"  # Ячейка с адресом (первый столбец)
SAVE_BUTTON = "#saveAccountingObjectModalForm > div.rt-form-footer > button.ant-btn.ant-btn-primary"  # Кнопка сохранить
INFO_TEXT = "#saveAccountingObjectModalForm > div.rt-form-body > div.checkAndInfoArea span"  # Информационный текст

# ============================================
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# ============================================

# Глобальный счетчик и хранилище для ошибок
error_log = {
    "total_errors_found": 0,
    "errors_closed": 0,
    "errors_details": []
}

# Текущий контекст выполнения
current_action_context = "Начало теста"

# Результаты теста
test_results = {
    "selected_object_index": None,
    "deleted_address": None,
    "type_attempts": [],
    "save_success": False,
    "final_type": None,
    "save_button_active_on_row": None,
    "rows_per_type": {}  # Для хранения количества строк для каждого типа
}


# ============================================
# ФУНКЦИИ ДЛЯ УМНОГО ОЖИДАНИЯ И ЗАКРЫТИЯ ОШИБОК
# ============================================

def try_close_error():
    """Пытается закрыть ошибку по крестику"""
    try:
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
    """Проверяет наличие стойких ошибок, которые можно закрыть"""
    global current_action_context
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
                            # Закрываем ТОЛЬКО если это реальная ошибка
                            if ("не обнаружено" not in text_lower and
                                    "не найдено" not in text_lower and
                                    "успешно" not in text_lower and
                                    "успешн" not in text_lower and
                                    "завершено" not in text_lower and
                                    "completed" not in text_lower and
                                    "готово" not in text_lower):

                                # Сохраняем информацию об ошибке с контекстом
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
    """Умное ожидание исчезновения ошибок на странице с возможностью закрытия"""
    print(f"\nУмное ожидание исчезновения ошибок...")

    start_wait_time = time.time()
    max_wait_time = 5
    errors_found_in_this_wait = 0

    try:
        while time.time() - start_wait_time < max_wait_time:
            if check_for_persistent_errors():
                errors_found_in_this_wait += 1
                elapsed = time.time() - start_wait_time
                if elapsed > 0.5:
                    print(f"  Ошибка держится {elapsed:.1f}с, пробуем закрыть...")
                    if try_close_error():
                        print(f"  Попытка закрытия выполнена")
                        time.sleep(0.5)
                    else:
                        print(f"  Не удалось найти кнопку закрытия")
                time.sleep(0.5)
            else:
                if errors_found_in_this_wait > 0:
                    print(f"  Все ошибки обработаны (найдено: {errors_found_in_this_wait})")
                else:
                    print(f"Ошибки не обнаружены")
                return True

        print(f"Ошибки не исчезли за {max_wait_time} секунд, продолжаем...")
        return False
    except Exception as e:
        print(f"Исключение в умном ожидании: {e}")
        return False


def wait_for_page_load(context=""):
    """Ожидание загрузки данных на странице"""
    global current_action_context
    if context:
        current_action_context = f"Загрузка страницы: {context}"

    print("Ожидание загрузки данных...")
    load_start = time.time()

    try:
        loading_selectors = [
            "div.ant-spin.ant-spin-spinning",
            "div.ant-spin-spinning",
            "span.anticon-loading.anticon-spin"
        ]

        for selector in loading_selectors:
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


def click_element(selector, element_name, context="", timeout=10):
    """Кликает на элемент по селектору"""
    global current_action_context
    if context:
        current_action_context = context
    else:
        current_action_context = f"Клик на '{element_name}'"

    try:
        element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        element.click()
        print(f"✓ {element_name}")
        time.sleep(0.5)
        smart_wait_for_errors_disappear()
        return True
    except Exception as e:
        print(f"✗ Не удалось кликнуть на {element_name}: {e}")
        smart_wait_for_errors_disappear()
        return False


def click_svg_element(svg_selector, action_name, context=""):
    """Кликает на SVG элемент (специально для кнопки действия)"""
    global current_action_context
    if context:
        current_action_context = context
    else:
        current_action_context = f"Клик на SVG: {action_name}"

    try:
        svg_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, svg_selector))
        )

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", svg_element)
        time.sleep(0.3)

        try:
            parent_button = svg_element.find_element(By.XPATH, "..")
            actions = ActionChains(driver)
            actions.move_to_element(parent_button).click().perform()
            print(f"✓ {action_name} (через родительский элемент)")
            time.sleep(0.5)
            smart_wait_for_errors_disappear()
            return True
        except:
            actions = ActionChains(driver)
            actions.move_to_element(svg_element).click().perform()
            print(f"✓ {action_name} (непосредственно на SVG)")
            time.sleep(0.5)
            smart_wait_for_errors_disappear()
            return True

    except Exception as e:
        print(f"✗ Не удалось {action_name}: {e}")
        smart_wait_for_errors_disappear()
        return False


def send_keys_to_element(selector, text, element_name, context=""):
    """Вводит текст в поле"""
    global current_action_context
    if context:
        current_action_context = context
    else:
        current_action_context = f"Ввод текста в '{element_name}'"

    try:
        element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        element.click()
        time.sleep(0.3)
        element.clear()
        time.sleep(0.3)
        element.send_keys(text)
        print(f"✓ Введен текст в {element_name}: '{text}'")
        time.sleep(0.5)
        smart_wait_for_errors_disappear()
        return True
    except Exception as e:
        print(f"✗ Ошибка при вводе текста в {element_name}: {e}")
        smart_wait_for_errors_disappear()
        return False


def get_random_row_index():
    """Получает случайный индекс строки из таблицы"""
    global current_action_context
    current_action_context = "Получение случайного индекса строки"

    try:
        table_body = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body"))
        )

        rows = table_body.find_elements(By.CSS_SELECTOR, ".BaseTable__row")

        if not rows:
            print("✗ Таблица пуста")
            return None

        row_count = len(rows)
        random_index = random.randint(1, row_count)
        print(f"✓ Выбран случайный индекс: {random_index} из {row_count}")
        return random_index

    except Exception as e:
        print(f"✗ Ошибка при получении случайного индекса: {e}")
        smart_wait_for_errors_disappear()
        return None


def select_object_by_index(index):
    """Выбирает объект по индексу через чекбокс"""
    global current_action_context
    current_action_context = f"Выбор объекта с индексом {index}"

    checkbox_selector = CHECKBOX_SELECTOR_TEMPLATE.format(index)
    return click_element(checkbox_selector, f"Выбрать объект с индексом {index}", current_action_context)


def open_action_menu():
    """Открывает меню действия через клик на SVG"""
    global current_action_context
    current_action_context = "Открытие меню действия"

    return click_svg_element(ACTION_MENU_SELECTOR, "Открыть меню действия", current_action_context)


def delete_selected_object():
    """Удаляет выбранный объект"""
    global current_action_context, test_results
    current_action_context = "Удаление выбранного объекта"

    # Открываем меню действия
    if not open_action_menu():
        print("✗ Не удалось открыть меню действия")
        return False

    time.sleep(1)
    smart_wait_for_errors_disappear()

    # Выбираем пункт "Удалить" (индекс 3)
    if not click_element(DELETE_MENU_ITEM_SELECTOR, "Выбрать пункт 'Удалить'", current_action_context):
        return False

    time.sleep(1)
    smart_wait_for_errors_disappear()

    # Получаем адрес из модального окна
    try:
        address_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, DELETE_MODAL_ADDRESS))
        )
        deleted_address = address_element.text.strip()
        test_results["deleted_address"] = deleted_address
        print(f"✓ Адрес удаляемого объекта: '{deleted_address}'")
    except Exception as e:
        print(f"✗ Не удалось получить адрес удаляемого объекта: {e}")
        smart_wait_for_errors_disappear()

    # Нажимаем кнопку удалить
    if not click_element(DELETE_BUTTON, "Нажать кнопку 'Удалить'", current_action_context):
        return False

    print("✓ Объект успешно удален")
    wait_for_page_load("после удаления объекта")
    return True


def create_new_object():
    """Создает новый объект"""
    global current_action_context
    current_action_context = "Создание нового объекта"

    # Открываем меню действия
    if not open_action_menu():
        print("✗ Не удалось открыть меню действия")
        return False

    time.sleep(1)
    smart_wait_for_errors_disappear()

    # Выбираем пункт "Создать" (индекс 1)
    if not click_element(CREATE_MENU_ITEM_SELECTOR, "Выбрать пункт 'Создать'", current_action_context):
        return False

    time.sleep(1)
    smart_wait_for_errors_disappear()
    return True


def select_object_type_by_index(type_index):
    """Выбирает тип объекта по индексу (1, 2 или 3)"""
    global current_action_context
    type_names = {1: "Тепловой пункт", 2: "Присоединенное строение", 3: "Источник теплоснабжения"}
    type_name = type_names.get(type_index, f"Тип {type_index}")

    current_action_context = f"Выбор типа объекта по индексу {type_index}: '{type_name}'"

    try:
        # Находим поле типа
        type_field = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, TYPE_FIELD))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", type_field)
        time.sleep(0.3)
        type_field.click()
        print(f"✓ Кликнули на поле типа для открытия списка")
        time.sleep(1)

        # Ждем появления выпадающего списка
        dropdown = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, TYPE_DROPDOWN))
        )

        # Находим все опции
        options = dropdown.find_elements(By.CSS_SELECTOR, TYPE_OPTION)

        if len(options) >= type_index:
            # Выбираем опцию по индексу (индексация с 1)
            option = options[type_index - 1]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
            time.sleep(0.3)
            option.click()
            print(f"✓ Выбран тип {type_index}: '{type_name}'")

            time.sleep(1)
            smart_wait_for_errors_disappear()
            return True
        else:
            print(f"✗ Не найдена опция с индексом {type_index}")
            return False

    except Exception as e:
        print(f"✗ Ошибка при выборе типа с индексом {type_index}: {e}")
        smart_wait_for_errors_disappear()
        return False


def enter_address(address):
    """Вводит адрес в поле"""
    return send_keys_to_element(ADDRESS_INPUT, address, "поле адреса", f"Ввод адреса: '{address}'")


def get_table_rows():
    """Получает все строки из таблицы добавления"""
    global current_action_context
    current_action_context = "Получение строк таблицы"

    try:
        rows = driver.find_elements(By.CSS_SELECTOR, TABLE_ROWS)
        print(f"✓ Найдено строк в таблице добавления: {len(rows)}")
        return rows
    except Exception as e:
        print(f"✗ Ошибка при получении строк таблицы: {e}")
        smart_wait_for_errors_disappear()
        return []


def get_address_from_row(row):
    """Получает адрес из строки таблицы"""
    try:
        # Ищем ячейку с адресом (первый столбец)
        address_cell = row.find_element(By.CSS_SELECTOR, TABLE_CELL_ADDRESS)
        address_text = address_cell.text.strip()
        return address_text
    except:
        # Если не нашли по специальному селектору, пробуем получить текст всей строки
        try:
            full_text = row.text
            # Предполагаем, что адрес - это первая строка или часть текста
            lines = full_text.split('\n')
            if lines:
                return lines[0].strip()
        except:
            pass
    return None


def check_address_match(row, expected_address, row_index):
    """Проверяет, совпадает ли адрес в строке с ожидаемым"""
    global current_action_context
    current_action_context = f"Проверка адреса в строке {row_index}"

    row_address = get_address_from_row(row)

    if not row_address:
        print(f"✗ Не удалось получить адрес из строки {row_index}")
        return False

    if expected_address in row_address or row_address in expected_address:
        print(f"✓ Адрес в строке {row_index} совпадает: '{row_address}'")
        return True
    else:
        print(f"✗ Адрес в строке {row_index} НЕ совпадает:")
        print(f"   Ожидаемый: '{expected_address}'")
        print(f"   Фактический: '{row_address}'")
        return False


def click_table_row(row, row_index):
    """Кликает на конкретную строку таблицы"""
    global current_action_context
    current_action_context = f"Клик на строку таблицы {row_index}"

    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", row)
        time.sleep(0.2)
        row.click()
        print(f"✓ Кликнули на строку {row_index}")
        time.sleep(1)  # Ждем секунду после клика как требуется
        smart_wait_for_errors_disappear()
        return True
    except Exception as e:
        print(f"✗ Не удалось кликнуть на строку {row_index}: {e}")
        smart_wait_for_errors_disappear()
        return False


def is_save_button_enabled():
    """Проверяет, активна ли кнопка Сохранить"""
    global current_action_context
    current_action_context = "Проверка доступности кнопки Сохранить"

    try:
        save_button = driver.find_element(By.CSS_SELECTOR, SAVE_BUTTON)
        is_enabled = save_button.is_enabled() and "disabled" not in save_button.get_attribute("class")

        if is_enabled:
            print("✓ Кнопка 'Сохранить' активна")
        else:
            print("✗ Кнопка 'Сохранить' неактивна")

        return is_enabled

    except Exception as e:
        print(f"✗ Ошибка при проверке кнопки Сохранить: {e}")
        smart_wait_for_errors_disappear()
        return False


def get_info_text():
    """Получает информационный текст"""
    try:
        info_element = driver.find_element(By.CSS_SELECTOR, INFO_TEXT)
        info_text = info_element.text.strip()
        print(f"✓ Информация: '{info_text}'")
        return info_text
    except:
        return None


def click_save():
    """Нажимает кнопку Сохранить"""
    global current_action_context, test_results
    current_action_context = "Сохранение объекта"

    if click_element(SAVE_BUTTON, "Нажать кнопку 'Сохранить'", current_action_context):
        print("✓ Объект успешно сохранен")
        test_results["save_success"] = True
        wait_for_page_load("после сохранения объекта")
        return True
    else:
        return False


# ============================================
# ОСНОВНОЙ СКРИПТ
# ============================================

print("=" * 60)
print("ТЕСТ: Создание объекта теплосети после удаления")
print("=" * 60)

# 1. АВТОРИЗАЦИЯ
print("\n" + "=" * 50)
print("ШАГ 1: АВТОРИЗАЦИЯ")
print("=" * 50)

try:
    current_action_context = "Авторизация в системе"
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
print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ 'ОБЪЕКТЫ ТЕПЛОСЕТИ'")
print("=" * 50)

try:
    current_action_context = "Переход в раздел Объекты теплосети"
    driver.get('http://10.5.121.74/predbilling/accountingObjectsPredBill')
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("✓ Переход в раздел 'Объекты теплосети'")
    time.sleep(2)
    smart_wait_for_errors_disappear()
    wait_for_page_load("после перехода в раздел")
except Exception as e:
    print(f"✗ Не удалось перейти в раздел: {e}")
    driver.quit()
    exit()

# 3. ВЫБОР СЛУЧАЙНОГО ОБЪЕКТА
print("\n" + "=" * 50)
print("ШАГ 3: ВЫБОР СЛУЧАЙНОГО ОБЪЕКТА")
print("=" * 50)

random_index = get_random_row_index()
if random_index:
    test_results["selected_object_index"] = random_index
    if select_object_by_index(random_index):
        print(f"✓ Объект с индексом {random_index} выбран")
    else:
        print(f"✗ Не удалось выбрать объект с индексом {random_index}")
        driver.quit()
        exit()
else:
    print("✗ Не удалось получить случайный индекс")
    driver.quit()
    exit()

# 4. УДАЛЕНИЕ ВЫБРАННОГО ОБЪЕКТА
print("\n" + "=" * 50)
print("ШАГ 4: УДАЛЕНИЕ ВЫБРАННОГО ОБЪЕКТА")
print("=" * 50)

if not delete_selected_object():
    print("✗ Не удалось удалить объект")
    driver.quit()
    exit()

# 5. СОЗДАНИЕ НОВОГО ОБЪЕКТА
print("\n" + "=" * 50)
print("ШАГ 5: СОЗДАНИЕ НОВОГО ОБЪЕКТА")
print("=" * 50)

if not create_new_object():
    print("✗ Не удалось открыть форму создания")
    driver.quit()
    exit()

# Выводим информационный текст
info_text = get_info_text()

# 6. ПОСЛЕДОВАТЕЛЬНЫЙ ПЕРЕБОР ВСЕХ ТРЕХ ТИПОВ ОБЪЕКТОВ
print("\n" + "=" * 50)
print("ШАГ 6: ПОСЛЕДОВАТЕЛЬНЫЙ ПЕРЕБОР ВСЕХ ТРЕХ ТИПОВ ОБЪЕКТОВ")
print("=" * 50)

save_button_enabled = False
selected_type_index = None
selected_type_name = None
active_row = None
address_already_entered = False

# Проходим по каждому индексу типа (1, 2, 3)
for type_index in [1, 2, 3]:
    type_names = {1: "Тепловой пункт", 2: "Присоединенное строение", 3: "Источник теплоснабжения"}
    type_name = type_names[type_index]

    print(f"\n{'=' * 60}")
    print(f"ТИП {type_index} ИЗ 3: '{type_name}'")
    print(f"{'=' * 60}")

    # 6.1. Выбираем тип по индексу
    if not select_object_type_by_index(type_index):
        print(f"✗ Не удалось выбрать тип {type_index}")
        test_results["type_attempts"].append({
            "type": type_name,
            "success": False,
            "error": f"Не удалось выбрать тип с индексом {type_index}"
        })
        continue

    time.sleep(1)

    # 6.2. Вводим адрес (только для первого типа, для остальных адрес уже есть)
    if test_results["deleted_address"] and not address_already_entered:
        if not enter_address(test_results["deleted_address"]):
            print("✗ Не удалось ввести адрес")
            driver.quit()
            exit()
        address_already_entered = True
        print("✓ Адрес введен (сохраняется для всех типов)")
    else:
        print("✓ Адрес уже введен (используется сохраненный)")

    time.sleep(1)

    # 6.3. Получаем строки таблицы
    rows = get_table_rows()
    test_results["rows_per_type"][type_name] = len(rows)

    if not rows:
        print(f"  ⚠ Таблица добавления пуста для типа '{type_name}'")
        test_results["type_attempts"].append({
            "type": type_name,
            "success": False,
            "error": "Таблица пуста"
        })
        continue

    # 6.4. Последовательно кликаем по каждой строке и проверяем адрес и кнопку
    row_clicked_success = False
    for i, row in enumerate(rows, 1):
        print(f"\n  --- Строка {i} из {len(rows)} ---")

        # Проверяем, что адрес в строке совпадает с введенным
        if not check_address_match(row, test_results["deleted_address"], i):
            print(f"  ⚠ Пропускаем строку {i} - адрес не совпадает")
            continue

        # Кликаем на строку
        if not click_table_row(row, i):
            continue

        row_clicked_success = True

        # Проверяем кнопку Сохранить
        if is_save_button_enabled():
            save_button_enabled = True
            selected_type_index = type_index
            selected_type_name = type_name
            active_row = i
            test_results["final_type"] = type_name
            test_results["save_button_active_on_row"] = i
            print(f"\n✓ КНОПКА 'СОХРАНИТЬ' СТАЛА АКТИВНОЙ!")
            print(f"   Тип {type_index}: '{type_name}'")
            print(f"   Строка: {i}")
            print(f"   Адрес в строке совпадает с введенным")

            # Сохраняем успешную попытку
            test_results["type_attempts"].append({
                "type": type_name,
                "success": True,
                "row": i,
                "address_matched": True
            })
            break
        else:
            print(f"  Кнопка неактивна на строке {i}")

    # Если кнопка стала активной - сохраняем и выходим
    if save_button_enabled:
        print(f"\n✓ Найден подходящий тип: {selected_type_index} - '{selected_type_name}' на строке {active_row} с совпадающим адресом")
        break

    # Если не удалось кликнуть ни на одну строку с совпадающим адресом
    if not row_clicked_success:
        test_results["type_attempts"].append({
            "type": type_name,
            "success": False,
            "error": "Не найдено строк с совпадающим адресом или не удалось кликнуть"
        })

    print(f"\n--- Тип {type_index} - '{type_name}' не подошел, переходим к следующему ---")

# 7. СОХРАНЕНИЕ ОБЪЕКТА (если кнопка стала активной)
print("\n" + "=" * 50)
print("ШАГ 7: СОХРАНЕНИЕ ОБЪЕКТА")
print("=" * 50)

if save_button_enabled and selected_type_name:
    print(f"✓ Кнопка активна на типе {selected_type_index} - '{selected_type_name}', строка {active_row} (адрес совпадает)")
    if click_save():
        print(f"✓ Объект успешно сохранен с типом '{selected_type_name}'")
    else:
        print(f"✗ Не удалось сохранить объект с типом '{selected_type_name}'")
else:
    # Если после проверки ВСЕХ ТРЕХ типов кнопка так и не стала активной
    error_msg = f"Кнопка 'Сохранить' так и не стала активной. Проверены все 3 типа"
    print(f"✗ {error_msg}")
    current_action_context = "Ошибка: кнопка Сохранить неактивна после всех трех типов"

    # Добавляем в лог ошибок
    error_log["total_errors_found"] += 1
    error_log["errors_details"].append({
        "time": time.strftime("%H:%M:%S"),
        "context": "Проверка доступности кнопки Сохранить",
        "text": error_msg
    })

# 8. ИТОГОВЫЙ ОТЧЕТ
print("\n" + "=" * 80)
print("ИТОГОВЫЙ ОТЧЕТ")
print("=" * 80)

print(f"\nРЕЗУЛЬТАТЫ ТЕСТА:")
print("-" * 40)
print(f"Выбранный индекс объекта: {test_results['selected_object_index']}")
print(f"Адрес удаленного объекта: '{test_results['deleted_address']}'")

print(f"\nПРОВЕРЕННЫЕ ТИПЫ (всего {len(test_results['type_attempts'])} из 3):")
for i, attempt in enumerate(test_results["type_attempts"], 1):
    status = "✓" if attempt.get("success") else "✗"
    print(f"  {i}. {status} {attempt['type']}")
    if attempt.get("success") and "row" in attempt:
        print(f"     ✓ Активна на строке: {attempt['row']}")
        print(f"     ✓ Адрес совпадает")
    if not attempt.get("success") and "error" in attempt:
        print(f"     ✗ Ошибка: {attempt['error']}")

print(f"\nСТАТИСТИКА ПО ТИПАМ:")
for type_name, row_count in test_results["rows_per_type"].items():
    print(f"  • {type_name}: {row_count} строк в таблице")

if test_results['final_type']:
    print(f"\nИТОГОВЫЙ ТИП: {test_results['final_type']}")
    print(f"Кнопка стала активна на строке: {test_results['save_button_active_on_row']}")
    print(f"Адрес в строке совпадает с введенным")
else:
    print(f"\nИТОГОВЫЙ ТИП: Не выбран (ни один тип не подошел)")

print(f"СОХРАНЕНИЕ: {'УСПЕШНО' if test_results['save_success'] else 'НЕ ВЫПОЛНЕНО'}")

# ВЫВОД ИНФОРМАЦИИ ОБ ОШИБКАХ
print(f"\nИНФОРМАЦИЯ ОБ ОШИБКАХ:")
print("-" * 40)
print(f"  • Всего ошибок найдено: {error_log['total_errors_found']}")
print(f"  • Успешно закрыто: {error_log['errors_closed']}")

if error_log['errors_details']:
    print(f"  • Детали ошибок:")
    for i, err in enumerate(error_log['errors_details'], 1):
        print(f"    {i}. [{err['time']}] {err['context']}")
        print(f"       Текст: {err['text']}")
else:
    print(f"  • Детали ошибок: не зафиксировано")

print(f"\nОБЩИЙ ИТОГ:")
print("-" * 40)

test_passed = test_results["save_success"]
if test_passed:
    print("✓ ТЕСТ ПРОЙДЕН УСПЕШНО!")
    print(f"  Объект сохранен с типом '{test_results['final_type']}' на строке {test_results['save_button_active_on_row']}")
    print(f"  Адрес в строке совпадает с введенным: '{test_results['deleted_address']}'")
else:
    print("✗ ТЕСТ НЕ ПРОЙДЕН - объект не сохранен ни с одним из трех типов")

print("=" * 80)

# Закрытие браузера
try:
    print("\nЗакрытие браузера...")
    time.sleep(2)
    driver.quit()
    print("✓ Браузер успешно закрыт")
except Exception as e:
    print(f"✗ Не удалось закрыть браузер: {e}")