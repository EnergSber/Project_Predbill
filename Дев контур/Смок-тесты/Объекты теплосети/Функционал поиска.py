"""
"РЕЕСТР ОБЪЕКТОВ ТЕПЛОСЕТИ" проверка поиска

тестирование функциональности веб-приложения, включая:
1. Авторизацию в системе
2. Поиск данных по адресу

ОСНОВНЫЕ ВОЗМОЖНОСТИ:
---------------------
1. ПОИСКОВЫЙ ТЕСТ:
   - Поиск по адресу
   - Проверка корректности результатов поиска

ТЕХНИЧЕСКИЕ ОСОБЕННОСТИ:
------------------------
- Использует Selenium WebDriver для автоматизации браузера
- Реализованы "умные" ожидания элементов (WebDriverWait)
- Обработка динамических элементов и AJAX-загрузок
- Подробное логирование всех действий и результатов
- Умное ожидание исчезновения ошибок с возможностью закрытия только ошибочных уведомлений

СТРУКТУРА ТЕСТОВ:
-----------------
1. Подготовительные шаги (авторизация, переход в раздел, фильтрация)
2. Тест поиска по адресу (с проверкой результатов)
3. Итоговый отчет с детализацией результатов

ВЫВОД РЕЗУЛЬТАТОВ:
------------------
- Подробное логирование в консоль
- Итоговый статус теста
- Общий итог тестирования
- Детальная информация о найденных ошибках с указанием контекста
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

# Инициализация драйвера
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()
wait = WebDriverWait(driver, 60)

# Данные для авторизации
from config import USERNAME, PASSWORD

URL = 'http://10.5.121.74/login'

# ============================================
# СЕЛЕКТОРЫ (адаптированы из реестра водомеров и экспорта объектов)
# ============================================

# Основные селекторы (из реестра водомеров)
FILTER_SELECTOR = "svg[data-icon='filter']"
RESET_SELECTOR = "svg[data-icon='stop']"
APPLY_SELECTOR = "svg[data-icon='check']"

# Селекторы для поля поиска (из реестра водомеров)
SEARCH_INPUT_WRAPPER = "span.ant-input-affix-wrapper"
SEARCH_INPUT_SELECTOR = "span.ant-input-affix-wrapper input.ant-input[placeholder='Поиск по адресу']"
SEARCH_CLEAR_SELECTOR = "span.ant-input-affix-wrapper span.ant-input-clear-icon"
SEARCH_CLEAR_ICON = "span.ant-input-clear-icon svg[data-icon='close-circle']"

# Селекторы таблицы для объектов теплосети (из экспорта объектов)
TABLE_SELECTOR = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body"
TABLE_HEADER_SELECTOR = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__header"

# Селектор кнопки применения фильтра для объектов теплосети (из экспорта объектов)
APPLY_BUTTON_SELECTOR = "button[section='accountingObjectsPredBill']"

# Данные для поиска (тот же адрес что и в водомерах)
SEARCH_ADDRESS = "1-й Амбулаторный пр., д.2/6"

# ============================================
# ФУНКЦИИ ДЛЯ УМНОГО ОЖИДАНИЯ И ЗАКРЫТИЯ ОШИБОК
# ============================================

# Глобальный счетчик и хранилище для ошибок
error_log = {
    "total_errors_found": 0,
    "errors_closed": 0,
    "errors_details": []
}

# Текущий контекст выполнения
current_action_context = "Начало теста"


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
                                    "text": error_text[:200]  # Ограничиваем длину
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


# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ПОИСКОМ
# ============================================

def perform_search(search_value):
    """Выполняет поиск по указанному адресу"""
    global current_action_context
    current_action_context = f"Поиск по адресу: '{search_value}'"

    print(f"Выполняем поиск по адресу: '{search_value}'")

    try:
        input_element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, SEARCH_INPUT_SELECTOR))
        )
        input_element.click()
        time.sleep(0.5)
        input_element.clear()
        time.sleep(0.3)
        input_element.send_keys(search_value)
        time.sleep(0.5)
        input_element.send_keys(Keys.ENTER)
        print("Поиск выполнен")
        smart_wait_for_errors_disappear()
        return True

    except Exception as e:
        print(f"Ошибка при выполнении поиска: {e}")
        smart_wait_for_errors_disappear()
        return False


def clear_search():
    """Очищает поле поиска нажатием на крестик"""
    global current_action_context
    current_action_context = "Очистка поля поиска"

    print("Очищаем поле поиска...")

    try:
        clear_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, SEARCH_CLEAR_SELECTOR))
        )
        if "hidden" not in clear_button.get_attribute("class"):
            clear_button.click()
            print("Поле поиска очищено через крестик")
            smart_wait_for_errors_disappear()
            return True
        else:
            print("Крестик скрыт (поле пустое)")
            return True

    except Exception as e:
        print(f"Не удалось очистить через крестик: {e}")
        smart_wait_for_errors_disappear()
        return False


def check_table_for_value(search_value, expected_column="Адрес"):
    """Проверяет таблицу на наличие указанного значения"""
    global current_action_context
    current_action_context = f"Проверка таблицы на наличие '{search_value}'"

    print(f"Проверяем таблицу на наличие значения: '{search_value}'")

    try:
        table_body = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, TABLE_SELECTOR))
        )

        rows = table_body.find_elements(By.CSS_SELECTOR, ".BaseTable__row")

        if not rows:
            print("Таблица пуста после поиска")
            smart_wait_for_errors_disappear()
            return False, 0, []

        print(f"Найдено строк в таблице: {len(rows)}")

        # Находим индекс столбца "Адрес"
        column_index = None
        try:
            header = driver.find_element(By.CSS_SELECTOR, TABLE_HEADER_SELECTOR)
            header_cells = header.find_elements(By.CSS_SELECTOR, ".BaseTable__header-cell")

            for i, cell in enumerate(header_cells):
                cell_text = cell.text.strip()
                if expected_column in cell_text:
                    column_index = i
                    print(f"Найден столбец '{expected_column}' с индексом в коде: {i} (в таблице: {i + 1})")
                    break
        except:
            print("Не удалось определить индекс столбца")

        mismatched_rows = []

        for i, row in enumerate(rows, 1):
            try:
                if column_index is not None:
                    cells = row.find_elements(By.CSS_SELECTOR, ".BaseTable__row-cell")
                    if len(cells) > column_index:
                        cell_text = cells[column_index].text.strip()
                        contains_value = search_value in cell_text
                    else:
                        contains_value = search_value in row.text
                else:
                    contains_value = search_value in row.text

                if not contains_value:
                    mismatched_rows.append(i)
                    if len(mismatched_rows) <= 3:
                        print(f"  Строка {i}: НЕ содержит значение '{search_value}'")
            except Exception as e:
                print(f"  Ошибка при проверке строки {i}: {e}")
                mismatched_rows.append(i)

        if mismatched_rows:
            print(f"НАЙДЕНЫ НЕСООТВЕТСТВИЯ:")
            print(f"   Всего строк: {len(rows)}")
            print(f"   Строк с несоответствием: {len(mismatched_rows)}")
            smart_wait_for_errors_disappear()
            return False, len(rows), mismatched_rows
        else:
            print(f"ВСЕ СТРОКИ СООТВЕТСТВУЮТ!")
            print(f"   Всего строк: {len(rows)}")
            smart_wait_for_errors_disappear()
            return True, len(rows), []

    except Exception as e:
        print(f"Ошибка при проверке таблицы: {e}")
        smart_wait_for_errors_disappear()
        return False, 0, []


def click_element(selector, element_name):
    """Кликает на элемент по селектору"""
    global current_action_context
    current_action_context = f"Клик на '{element_name}'"

    try:
        element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        element.click()
        print(f"{element_name}")
        time.sleep(1)
        smart_wait_for_errors_disappear()
        return True
    except Exception as e:
        print(f"Не удалось кликнуть на {element_name}: {e}")
        smart_wait_for_errors_disappear()
        return False


def apply_filter_objects():
    """Специальная функция для применения фильтра объектов теплосети"""
    global current_action_context
    current_action_context = "Применение фильтра объектов теплосети"

    try:
        # Пробуем найти кнопку по специальному селектору
        apply_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, APPLY_BUTTON_SELECTOR))
        )
        apply_button.click()
        print("Кнопка применения фильтра нажата (по селектору button[section='accountingObjectsPredBill'])")
        time.sleep(1)
        smart_wait_for_errors_disappear()
        return True
    except:
        # Если не нашли, пробуем через общий селектор
        return click_element(APPLY_SELECTOR, "Кнопка применения фильтра (общий селектор)")


# ============================================
# ОСНОВНОЙ СКРИПТ
# ============================================

print("=" * 60)
print("ТЕСТ ПОИСКА ПО АДРЕСУ (РЕЕСТР ОБЪЕКТОВ ТЕПЛОСЕТИ)")
print("=" * 60)

results = {
    "preparation_steps": [],
    "search_test": None,
    "times": {}
}

# 1. АВТОРИЗАЦИЯ
print("=" * 50)
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
    print("Авторизация успешна")
    results["preparation_steps"].append("Авторизация - УСПЕШНО")
    smart_wait_for_errors_disappear()
except Exception as e:
    print(f"Авторизация не удалась: {e}")
    smart_wait_for_errors_disappear()
    driver.quit()
    exit()

# 2. ПЕРЕХОД В РАЗДЕЛ
print("=" * 50)
print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ 'РЕЕСТР ОБЪЕКТОВ ТЕПЛОСЕТИ'")
print("=" * 50)

try:
    current_action_context = "Переход в раздел Реестр объектов теплосети"
    driver.get('http://10.5.121.74/predbilling/accountingObjectsPredBill')
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("Переход в раздел 'Реестр объектов теплосети'")
    results["preparation_steps"].append("Переход в раздел - УСПЕШНО")
    time.sleep(2)
    smart_wait_for_errors_disappear()
except Exception as e:
    print(f"Не удалось перейти в раздел: {e}")
    smart_wait_for_errors_disappear()
    driver.quit()
    exit()

# 3. ОТКРЫТИЕ ФИЛЬТРА
print("=" * 50)
print("ШАГ 3: ОТКРЫТИЕ ФИЛЬТРА")
print("=" * 50)

if click_element(FILTER_SELECTOR, "Открыли фильтр"):
    results["preparation_steps"].append("Открытие фильтра - УСПЕШНО")

# 4. СБРОС ФИЛЬТРОВ
print("=" * 50)
print("ШАГ 4: СБРОС ФИЛЬТРОВ")
print("=" * 50)

if click_element(RESET_SELECTOR, "Сбросили фильтры"):
    results["preparation_steps"].append("Сброс фильтров - УСПЕШНО")

# 5. ОЖИДАНИЕ ЗАГРУЗКИ ПОСЛЕ СБРОСА
print("=" * 50)
print("ШАГ 5: ОЖИДАНИЕ ЗАГРУЗКИ ДАННЫХ ПОСЛЕ СБРОСА")
print("=" * 50)

load_duration_reset = wait_for_page_load("после сброса")
results["times"]["После сброса"] = load_duration_reset

# 6. ПРИМЕНЕНИЕ ФИЛЬТРА (специальная функция для объектов)
print("=" * 50)
print("ШАГ 6: ПРИМЕНЕНИЕ ФИЛЬТРА")
print("=" * 50)

if apply_filter_objects():
    results["preparation_steps"].append("Применение фильтра - УСПЕШНО")

# 7. ОЖИДАНИЕ ЗАГРУЗКИ ПОСЛЕ ПРИМЕНЕНИЯ ФИЛЬТРА
print("=" * 50)
print("ШАГ 7: ОЖИДАНИЕ ЗАГРУЗКИ ДАННЫХ ПОСЛЕ ПРИМЕНЕНИЯ ФИЛЬТРА")
print("=" * 50)

load_duration_apply = wait_for_page_load("после применения фильтра")
results["times"]["После применения"] = load_duration_apply

# 8. ВЫПОЛНЕНИЕ ТЕСТА ПОИСКА ПО АДРЕСУ
print("=" * 50)
print("ШАГ 8: ВЫПОЛНЕНИЕ ТЕСТА ПОИСКА ПО АДРЕСУ")
print("=" * 50)

print(f"{'=' * 40}")
print(f"ТЕСТ ПОИСКА: ПО АДРЕСУ")
print(f"{'=' * 40}")

search_success = perform_search(SEARCH_ADDRESS)

print("Ожидаем загрузки данных...")
load_time = wait_for_page_load("после поиска")

check_success, total_rows, mismatched_rows = check_table_for_value(SEARCH_ADDRESS)

search_test_result = {
    "name": "ПОИСК ПО АДРЕСУ",
    "value": SEARCH_ADDRESS,
    "search_success": search_success,
    "check_success": check_success,
    "total_rows": total_rows,
    "mismatched_rows": len(mismatched_rows),
    "load_time": load_time
}

results["search_test"] = search_test_result

if check_success and total_rows > 0:
    print(f"ТЕСТ ПОИСКА ПО АДРЕСУ - ОК")
    print(f"   • Найдено строк: {total_rows}")
    print(f"   • Все строки содержат адрес: '{SEARCH_ADDRESS}'")
    print(f"   • Время загрузки: {load_time:.1f} сек")
else:
    print(f"ТЕСТ ПОИСКА ПО АДРЕСУ - НЕ ОК")
    print(f"   • Найдено строк: {total_rows}")
    print(f"   • Строк с несоответствием: {len(mismatched_rows)}")
    print(f"   • Время загрузки: {load_time:.1f} сек")

# Очищаем поле поиска
clear_search()
wait_for_page_load("после очистки поиска")
time.sleep(1)

# 9. ИТОГОВЫЙ ОТЧЕТ
print("=" * 60)
print("ИТОГОВЫЙ ОТЧЕТ")
print("=" * 60)

print(f"ПОДГОТОВИТЕЛЬНЫЕ ШАГИ:")
for i, step in enumerate(results["preparation_steps"], 1):
    print(f"  {i}. {step}")

print(f"ВРЕМЯ ВЫПОЛНЕНИЯ ПОДГОТОВКИ:")
for step_name, duration in results["times"].items():
    print(f"  • {step_name}: {duration:.1f} сек")

print(f"РЕЗУЛЬТАТ ТЕСТА ПОИСКА:")
print("-" * 80)

if results["search_test"]:
    test = results["search_test"]
    status = "ОК" if test["check_success"] and test["total_rows"] > 0 else "НЕ ОК"
    print(f"ТЕСТ: {test['name']}")
    print(f"  Статус: {status}")
    print(f"  Значение: '{test['value']}'")
    print(f"  Найдено строк: {test['total_rows']}")
    print(f"  Строк с несоответствием: {test['mismatched_rows']}")
    print(f"  Время загрузки: {test['load_time']:.1f} сек")

print("-" * 80)

# ВЫВОД ИНФОРМАЦИИ ОБ ОШИБКАХ
print(f"ИНФОРМАЦИЯ ОБ ОШИБКАХ:")
print("-" * 80)
print(f"  • Всего ошибок найдено: {error_log['total_errors_found']}")
print(f"  • Успешно закрыто: {error_log['errors_closed']}")

if error_log['errors_details']:
    print(f"  • Детали ошибок (где и когда возникли):")
    for i, err in enumerate(error_log['errors_details'], 1):
        print(f"    {i}. [{err['time']}] {err['context']}")
        print(f"       Текст: {err['text']}")
else:
    print(f"  • Детали ошибок: не зафиксировано")

print("-" * 80)

print(f"ОБЩИЙ ИТОГ:")
print("-" * 40)

preparation_ok = all(["УСПЕШНО" in step for step in results["preparation_steps"]])
search_ok = results["search_test"] and results["search_test"]["check_success"] and results["search_test"][
    "total_rows"] > 0

print(f"Подготовительные шаги: {'ок' if preparation_ok else 'не ок'}")
print(f"Тест поиска: {'ок' if search_ok else 'не ок'}")

all_tests_passed = preparation_ok and search_ok

if all_tests_passed:
    print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
else:
    print("ИМЕЮТСЯ ОШИБКИ В ВЫПОЛНЕНИИ")

print("-" * 40)
print(f"{'=' * 60}")

smart_wait_for_errors_disappear()

# Закрытие браузера
try:
    print("Закрытие браузера...")
    driver.quit()
    print("Браузер успешно закрыт")
except Exception as e:
    print(f"Не удалось закрыть браузер: {e}")