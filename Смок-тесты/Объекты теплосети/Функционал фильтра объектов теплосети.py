"""
ТЕСТОВЫЙ КЕЙС: Реестр объектов теплосети

ЦЕЛЬ: Проверка функциональности фильтрации в разделе "Объекты теплосети"

ОПИСАНИЕ ТЕСТА:
1. Авторизация в системе под пользователем predbill
2. Переход в раздел "Объекты теплосети"
3. Проверка на наличие ошибок на странице
4. Открытие фильтра и сброс перед заполнением
5. Последовательное заполнение всех полей фильтра:
   - Тип объекта (мультиселект, случайный выбор)
   - MUID (текстовое поле, ввод 22 случайных цифр)
   - Адрес (специальное поле с кликом рядом)
   - АО (мультиселект, случайный выбор)
   - Район (мультиселект, случайный выбор)
   - Номер ТП (текстовое поле, ввод значения)
   - Филиал (мультиселект, случайный выбор)
   - Предприятие (мультиселект, случайный выбор)
   - Прибор учёта: Наличие ПУ (селект, случайный выбор)
   - Прибор учёта: Номер ПУ (текстовое поле, ввод значения)
   - Прибор учёта: Марка ПУ (мультиселект, случайный выбор)
   - ЦТП/ИТП (мультиселект, случайный выбор)
6. Сброс фильтров и проверка очистки всех полей (с учетом плейсхолдеров)
7. Выбор случайного АО и проверка фильтрации данных в таблице
8. Финальный сброс фильтров и генерация отчета

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- Все поля фильтра корректно заполняются и сбрасываются
- Таблица данных корректно фильтруется по выбранному АО
- Отсутствие ошибок в процессе выполнения теста
- Корректная работа всех элементов интерфейса
- Все плейсхолдеры игнорируются при проверке сброса полей

ОСОБЕННОСТИ:
- Используются расширенные списки исключений для плейсхолдеров
- Особые обработчики для полей: адрес (с кликом рядом)
- Tab нажимается после каждого поля, кроме "Адрес"
- Подробное логирование каждого шага
- Проверка соответствия данных в таблице выбранному фильтру
- Валидация сброса всех полей с игнорированием стандартных плейсхолдеров
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

# Настройка браузера
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()
wait = WebDriverWait(driver, 60)

# Данные для авторизации
from config import USERNAME, PASSWORD
URL = 'http://10.5.121.74/login'


# Селекторы (как в реестре ведомостей)
FILTER_SELECTOR = "svg[data-icon='filter']"
APPLY_BUTTON_SELECTOR = "button[section='accountingObjectsPredBill'] span[role='img'][aria-label='check']"
RESET_BUTTON_SELECTOR = "button[type='button'] span[role='img'][aria-label='stop']"
TABLE_SELECTOR = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body"

# Хранение ошибок и пропущенных полей
section_errors = []
skipped_fields = []

# Храним выбранное АО для проверки
selected_ao_value = None

print("=" * 60)
print("ТЕСТ РАЗДЕЛА: Объекты теплосети")
print("=" * 60)


def click_svg_element(svg_selector, action_name):
    """Клик по SVG элементу"""
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
            print(f"{action_name} выполнен")
            time.sleep(0.5)
            return True
        except:
            actions = ActionChains(driver)
            actions.move_to_element(svg_element).click().perform()
            print(f"{action_name} выполнен")
            time.sleep(0.5)
            return True
    except Exception as e:
        print(f"Не удалось {action_name}: {e}")
        return False


def press_tab():
    """Нажимает клавишу Tab"""
    try:
        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB).perform()
        print("  Нажали Tab")
        time.sleep(0.3)
        return True
    except:
        return False


def add_error(error_text):
    """Добавляет ошибку в список"""
    if error_text not in section_errors:
        section_errors.append(error_text)
        print(f"  ❌ {error_text}")


def add_skipped_field(field_name, reason):
    """Добавляет пропущенное поле в список"""
    skipped_fields.append({"field": field_name, "reason": reason})
    print(f"  ⚠️ Пропущено поле '{field_name}': {reason}")


def try_close_errors():
    """Закрывает всплывающие ошибки"""
    try:
        close_selectors = [
            "span.ant-notification-notice-close-x",
            ".ant-notification-notice-close",
            ".ant-alert-close-icon",
            "[aria-label='close']",
            ".anticon-close"
        ]

        for selector in close_selectors:
            try:
                close_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in close_buttons:
                    try:
                        if btn.is_displayed() or btn.is_enabled():
                            actions = ActionChains(driver)
                            actions.move_to_element(btn).click().perform()
                            print(f"  Закрыта всплывающая ошибка")
                            time.sleep(0.2)
                            return True
                    except:
                        continue
            except:
                continue
        return False
    except Exception as e:
        print(f"  Ошибка при закрытии ошибок: {e}")
        return False


def wait_for_page_load():
    """Ожидает загрузки страницы"""
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
        return load_duration

    except Exception as e:
        print(f"  Ошибка при ожидании загрузки: {e}")
        return time.time() - load_start


def generate_random_muid():
    """Генерирует случайный MUID из 22 цифр"""
    return ''.join([str(random.randint(0, 9)) for _ in range(22)])


def find_field_by_label(label_text, action_type="select", value=None, select_all=False, exclude_select_all=True):
    """
    УНИВЕРСАЛЬНАЯ ФУНКЦИЯ: ищет поле по тексту лейбла и взаимодействует с ним

    Args:
        label_text: текст лейбла (например, "Тип объекта", "АО", "Адрес")
        action_type: "select" - для выпадающих списков,
                    "input" - для текстовых полей,
                    "address" - для адреса,
                    "single_select" - для одиночных селектов
        value: значение для ввода (для action_type="input")
        select_all: True - выбрать "Выбрать все" (для мультиселектов)
        exclude_select_all: True - исключать "Выбрать все" из списка (для мультиселектов)

    Returns:
        bool: успешность операции
    """
    try:
        print(f"\nИщем поле с лейблом: '{label_text}'")

        # Ищем лейбл по тексту
        label_xpath = f"//label[contains(text(), '{label_text}')]"
        label = wait.until(EC.presence_of_element_located((By.XPATH, label_xpath)))
        print(f"  Лейбл найден")

        # Находим родительский элемент строки
        row = label.find_element(By.XPATH, "./ancestor::div[contains(@class, 'ant-row')]")

        # Для поля адреса
        if action_type == "address":
            return process_address_field_by_label(label_text)

        # Для текстовых полей
        elif action_type == "input":
            # Ищем input внутри строки
            try:
                element = row.find_element(By.CSS_SELECTOR, "input")
                print(f"  Нашли input поле")
            except:
                print(f"  Не нашли input поле")
                add_skipped_field(label_text, "Поле ввода не найдено")
                return False

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)

            element.click()
            time.sleep(0.3)
            element.clear()
            time.sleep(0.3)
            element.send_keys(value)
            print(f"  Ввели значение: {value}")
            time.sleep(0.5)
            return True

        # Для выпадающих списков (мультиселект или одиночный)
        else:
            # Ищем кликабельный элемент для открытия списка
            try:
                # Пробуем найти селектор
                element = row.find_element(By.CSS_SELECTOR, "div.ant-select-selector")
            except:
                try:
                    element = row.find_element(By.CSS_SELECTOR, "div.ant-col.ant-col-14 > div > div > div")
                except:
                    print(f"  Не нашли кликабельный элемент")
                    add_skipped_field(label_text, "Кликабельный элемент не найден")
                    return False

            print(f"  Нашли выпадающий список")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            element.click()
            print(f"  Открыли выпадающий список")
            time.sleep(1)

            # Работа с выпадающим списком
            dropdown_selector = ".ant-select-dropdown:not(.ant-select-dropdown-hidden)"
            dropdown = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, dropdown_selector)))
            options = dropdown.find_elements(By.CSS_SELECTOR, ".ant-select-item-option")
            print(f"  Найдено опций: {len(options)}")

            if not options:
                print(f"  Список пуст")
                add_skipped_field(label_text, "Список пуст")
                return False

            if select_all:
                for option in options:
                    try:
                        option_text = option.text.strip()
                        if "Выбрать все" in option_text:
                            option.click()
                            print(f"  Выбрали 'Выбрать все'")
                            time.sleep(0.5)
                            return True
                    except:
                        continue
                print(f"  'Выбрать все' не найдено")
                add_skipped_field(label_text, "'Выбрать все' не найдено")
                return False
            else:
                valid_options = []
                for option in options:
                    try:
                        option_text = option.text.strip()
                        # Исключаем "Выбрать все" если нужно
                        if exclude_select_all and "Выбрать все" in option_text:
                            continue
                        if option_text:  # Только непустые
                            valid_options.append(option)
                    except:
                        continue

                if not valid_options:
                    print(f"  Нет доступных значений")
                    add_skipped_field(label_text, "Нет доступных значений")
                    return False

                random_option = random.choice(valid_options)
                random_text = random_option.text.strip()

                # Прокручиваем к выбранному элементу
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", random_option)
                time.sleep(0.3)

                random_option.click()
                print(f"  Выбрали: '{random_text}'")
                time.sleep(0.5)

                # Сохраняем значение для АО
                if label_text == "АО":
                    global selected_ao_value
                    selected_ao_value = random_text
                    print(f"  Сохранили АО для проверки: '{selected_ao_value}'")

                return True

    except Exception as e:
        print(f"Ошибка при обработке поля '{label_text}': {e}")
        add_skipped_field(label_text, str(e)[:100])
        return False


def process_address_field_by_label(label_text):
    """
    Специализированная функция для обработки поля адреса
    """
    try:
        print(f"\nОбрабатываем поле: {label_text}")

        # Находим лейбл и строку
        label_xpath = f"//label[contains(text(), '{label_text}')]"
        label = wait.until(EC.presence_of_element_located((By.XPATH, label_xpath)))
        row = label.find_element(By.XPATH, "./ancestor::div[contains(@class, 'ant-row')]")

        # Находим элемент адреса
        try:
            address_element = row.find_element(By.CSS_SELECTOR, "div.searchableSelectHeader")
            print(f"  Нашли поле адреса")
        except:
            print(f"  Не нашли поле адреса")
            add_skipped_field(label_text, "Поле адреса не найдено")
            return False

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", address_element)
        time.sleep(0.5)

        address_element.click()
        print(f"  Кликнули на поле адреса для раскрытия")
        time.sleep(2)

        # Ждем появления searchableSelectPopup
        popup_selector = "div.searchableSelectPopup"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, popup_selector)))
        print(f"  Появилось окно поиска адреса")
        time.sleep(1)

        # Находим поле ввода внутри popup
        input_selector = "div.searchableSelectPopupInsider div.searchBox.Адрес input.searchInput"
        try:
            search_input = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, input_selector))
            )
            print(f"  Нашли поле ввода адреса")
        except:
            print(f"  Не нашли поле ввода адреса")
            add_skipped_field(label_text, "Поле ввода не найдено")
            return False

        # Вводим адрес
        address_value = "1-й Амбулаторный пр., д.2/6"
        search_input.clear()
        time.sleep(0.3)
        search_input.send_keys(address_value)
        print(f"  Ввели адрес: {address_value}")
        time.sleep(3)

        # Ждем появления списка
        list_selector = "div.searchableSelectPopupInsider div.searchBox.Адрес ul.itemsList li"
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, list_selector)))
            address_items = driver.find_elements(By.CSS_SELECTOR, list_selector)
            print(f"  Найдено элементов в списке: {len(address_items)}")

            if address_items:
                # Ищем "Выбрать все"
                select_all_found = False
                for item in address_items:
                    item_text = item.text.strip()
                    if "Выбрать все" in item_text:
                        item.click()
                        print(f"  Выбрали: '{item_text}'")
                        select_all_found = True
                        break

                if not select_all_found and address_items:
                    # Если не нашли "Выбрать все", выбираем первый
                    first_item = address_items[0]
                    first_item_text = first_item.text.strip()
                    first_item.click()
                    print(f"  Выбрали первый элемент: '{first_item_text}'")
                time.sleep(1)

                # Кликаем на поле "Тип объекта" чтобы закрыть список
                try:
                    type_object = driver.find_element(By.XPATH, "//label[contains(text(), 'Тип объекта')]")
                    type_object.click()
                    print(f"  Кликнули на поле Тип объекта для закрытия списка")
                    time.sleep(0.5)
                except:
                    # Если не нашли, кликаем по координатам
                    actions = ActionChains(driver)
                    actions.move_by_offset(500, 200).click().perform()
                    print(f"  Кликнули по координатам для закрытия списка")
                    time.sleep(0.5)

                return True
            else:
                print(f"  Список адресов пуст")
                add_skipped_field(label_text, "Список адресов пуст")
                return False

        except Exception as e:
            print(f"  Не дождались появления списка адресов: {e}")
            add_skipped_field(label_text, f"Ошибка при выборе адреса: {str(e)[:100]}")
            return False

    except Exception as e:
        print(f"Ошибка при обработке поля адреса: {e}")
        add_skipped_field("Адрес", str(e)[:100])
        return False


def check_fields_emptiness():
    """
    Проверяет что все поля пустые после сброса фильтров
    Возвращает список полей которые не сбросились
    """
    print("\nПроверяем сброс всех полей фильтра...")

    not_emptied_fields = []

    # Список полей для проверки
    fields_to_check = [
        ("Тип объекта", "select"),
        ("MUID", "input"),
        ("Адрес", "address"),
        ("АО", "select"),
        ("Район", "select"),
        ("Номер ТП", "input"),
        ("Филиал", "select"),
        ("Предприятие", "select"),
        ("Наличие ПУ", "select"),
        ("Номер ПУ", "input"),
        ("Марка ПУ", "select"),
        ("ЦТП/ИТП", "select")
    ]

    # Плейсхолдеры для игнорирования
    placeholder_texts = [
        "Выберите значение", "Select value",
        "Выбрать все", "Select all",
        "Выберите", "Select",
        "Выберите...", "Select...",
        "Не выбрано", "Not selected",
        "Выберите из списка", "Select from list",
        "Значение не выбрано", "Value not selected",
        "Выбрать", "Choose",
        "Введите адрес", "Введите значение",
        "Введите MUID", "Введите номер",
        "Адрес", "Address",
        "Поиск адреса", "Search address"
    ]

    for field_name, field_type in fields_to_check:
        try:
            # Пытаемся найти поле по лейблу
            label_xpath = f"//label[contains(text(), '{field_name}')]"
            label = driver.find_element(By.XPATH, label_xpath)
            row = label.find_element(By.XPATH, "./ancestor::div[contains(@class, 'ant-row')]")

            if field_type == "input":
                element = row.find_element(By.CSS_SELECTOR, "input")
                field_value = element.get_attribute("value")
                if field_value and field_value.strip():
                    is_placeholder = any(ph in field_value for ph in placeholder_texts)
                    if not is_placeholder:
                        not_emptied_fields.append(f"{field_name}: {field_value}")
                        print(f"  {field_name}: '{field_value}'")
                    else:
                        print(f"  {field_name}: плейсхолдер")
                else:
                    print(f"  {field_name}: пустое")

            elif field_type == "address":
                try:
                    address_element = row.find_element(By.CSS_SELECTOR, "div.searchableSelectHeader")
                    field_text = address_element.text.strip()
                    if field_text and field_text != "Выбрать" and not any(ph in field_text for ph in placeholder_texts):
                        not_emptied_fields.append(f"Адрес: {field_text}")
                        print(f"  Адрес: '{field_text}'")
                    else:
                        print(f"  Адрес: пустое (Выбрать)")
                except:
                    print(f"  Адрес: поле не найдено")

            else:  # select
                try:
                    element = row.find_element(By.CSS_SELECTOR, "div.ant-select-selector")
                    field_text = element.text.strip()
                    is_placeholder = any(ph in field_text for ph in placeholder_texts)
                    if field_text and not is_placeholder:
                        not_emptied_fields.append(f"{field_name}: {field_text}")
                        print(f"  {field_name}: '{field_text}'")
                    else:
                        print(f"  {field_name}: пустое (плейсхолдер)")
                except:
                    print(f"  {field_name}: не удалось проверить")

        except Exception as e:
            print(f"  {field_name}: ошибка проверки - {str(e)[:50]}")
            continue

    return not_emptied_fields


def check_table_for_ao(selected_ao):
    """
    Проверяет таблицу на соответствие выбранному АО
    Возвращает (success, row_count)
    """
    try:
        print(f"\nПроверяем таблицу для АО: '{selected_ao}'")

        # Ждем загрузки таблицы
        print("Ожидание загрузки таблицы после применения фильтра...")
        time.sleep(2)
        wait_for_page_load()

        # Находим таблицу
        try:
            table_body = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, TABLE_SELECTOR))
            )
        except Exception as e:
            add_error(f"Не удалось найти таблицу: {e}")
            print(f"  Таблица не найдена")
            return False, 0

        # Получаем все строки таблицы
        rows = table_body.find_elements(By.CSS_SELECTOR, ".BaseTable__row")

        if not rows:
            add_error(f"Таблица пуста после применения фильтра с АО: '{selected_ao}'")
            print(f"  Таблица пуста")
            return False, 0

        print(f"  Найдено строк в таблице: {len(rows)}")

        # Проверяем каждую строку на наличие выбранного АО
        mismatched_rows = []
        for i, row in enumerate(rows, 1):
            try:
                row_text = row.text
                if selected_ao not in row_text:
                    mismatched_rows.append(i)
                    if len(mismatched_rows) <= 3:
                        print(f"    Строка {i}: НЕ содержит '{selected_ao}'")
                else:
                    if i <= 3:
                        print(f"    Строка {i}: содержит '{selected_ao}'")
            except:
                continue

        if mismatched_rows:
            error_msg = f"Найдены строки не соответствующие выбранному АО '{selected_ao}': строки {mismatched_rows[:5]}"
            if len(mismatched_rows) > 5:
                error_msg += f" и еще {len(mismatched_rows) - 5} строк"
            add_error(error_msg)
            print(f"  Найдено несоответствующих строк: {len(mismatched_rows)}")
            return False, len(rows)

        print(f"  Все строки ({len(rows)}) соответствуют выбранному АО: '{selected_ao}'")
        return True, len(rows)

    except Exception as e:
        add_error(f"Ошибка при проверке таблицы: {e}")
        print(f"  Ошибка проверки таблицы: {e}")
        return False, 0


def apply_filters():
    """Нажимает кнопку Применить (как в реестре ведомостей)"""
    try:
        print("\nПрименяем фильтры...")
        time.sleep(1)

        apply_svg = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, APPLY_BUTTON_SELECTOR))
        )

        parent_button = apply_svg.find_element(By.XPATH, "..")
        actions = ActionChains(driver)
        actions.move_to_element(parent_button).click().perform()
        print(f"  Нажали 'Применить'")
        return True

    except Exception as e:
        print(f"  Не удалось нажать 'Применить': {e}")
        add_error(f"Ошибка при применении фильтров: {e}")
        return False


def reset_filters():
    """Нажимает кнопку Сброс (как в реестре ведомостей)"""
    try:
        print("\nСбрасываем фильтры...")

        reset_svg = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, RESET_BUTTON_SELECTOR))
        )

        parent_button = reset_svg.find_element(By.XPATH, "..")
        actions = ActionChains(driver)
        actions.move_to_element(parent_button).click().perform()
        print(f"  Нажали 'Сброс'")
        time.sleep(1)
        return True

    except Exception as e:
        print(f"  Не удалось нажать 'Сброс': {e}")
        add_error(f"Ошибка при сбросе фильтров: {e}")
        return False


# ОСНОВНОЙ КОД
print("=" * 60)
print("ТЕСТ РАЗДЕЛА: Объекты теплосети")
print("=" * 60)

# 1. АВТОРИЗАЦИЯ
print("\n" + "=" * 50)
print("ШАГ 1: АВТОРИЗАЦИЯ")
print("=" * 50)

try:
    driver.get(URL)
    username_field = wait.until(EC.presence_of_element_located((By.ID, "normal_login_username")))
    username_field.send_keys(USERNAME)
    password_field = driver.find_element(By.ID, "normal_login_password")
    password_field.send_keys(PASSWORD)
    login_button = driver.find_element(By.CSS_SELECTOR, '.ant-btn.ant-btn-primary.w-100.mb-s')
    login_button.click()
    wait.until_not(EC.url_contains('login'))
    print("Авторизация успешна")
except Exception as e:
    print(f"Авторизация не удалась: {e}")
    driver.quit()
    exit()

# 2. ПЕРЕХОД В РАЗДЕЛ
print("\n" + "=" * 50)
print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ")
print("=" * 50)

section_url = 'http://10.5.121.74/predbilling/accountingObjectsPredBill'
section_name = 'Объекты теплосети'

try:
    driver.get(section_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print(f"Переход в раздел '{section_name}'")
    time.sleep(2)
except Exception as e:
    add_error(f"Не удалось перейти в раздел: {e}")
    driver.quit()
    exit()

# 3. ПРОВЕРКА ОШИБОК НА СТРАНИЦЕ
print("\n" + "=" * 50)
print("ШАГ 3: ПРОВЕРКА ОШИБОК НА СТРАНИЦЕ")
print("=" * 50)

error_found = False
error_selectors = [
    "div.ant-notification-notice-error",
    "div.ant-alert-error",
    ".ant-message-error",
    "[class*='error']",
    "[class*='danger']"
]

for selector in error_selectors:
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for elem in elements:
            try:
                if elem.is_displayed():
                    error_text = elem.text.strip()
                    if error_text and len(error_text) > 3:
                        add_error(f"Найдена ошибка на странице: {error_text}")
                        error_found = True
            except:
                continue
    except:
        continue

if not error_found:
    print("Явных ошибок не найдено")

try_close_errors()

# 4. ОТКРЫТИЕ ФИЛЬТРА
print("\n" + "=" * 50)
print("ШАГ 4: ОТКРЫТИЕ ФИЛЬТРА")
print("=" * 50)

filter_clicked = False
max_attempts = 3
time.sleep(2)

for attempt in range(max_attempts):
    if click_svg_element(FILTER_SELECTOR, f"Открыть фильтр (попытка {attempt + 1})"):
        filter_clicked = True
        break
    else:
        time.sleep(1)

if not filter_clicked:
    add_error("Не удалось открыть фильтр")
    driver.quit()
    exit()
else:
    print("Фильтр открыт")

time.sleep(2)

# 5. СБРОС ФИЛЬТРОВ ПЕРЕД ЗАПОЛНЕНИЕМ
print("\n" + "=" * 50)
print("ШАГ 5: СБРОС ФИЛЬТРОВ ПЕРЕД ЗАПОЛНЕНИЕМ")
print("=" * 50)

reset_clicked = reset_filters()
if not reset_clicked:
    add_error("Не удалось сбросить фильтры перед заполнением")

# Ожидание загрузки после сброса
load_duration = wait_for_page_load()

# 6. ЗАПОЛНЕНИЕ ПОЛЕЙ ФИЛЬТРА
print("\n" + "=" * 50)
print("ШАГ 6: ЗАПОЛНЕНИЕ ПОЛЕЙ ФИЛЬТРА")
print("=" * 50)

# Словарь для хранения результатов
results = {}

# Генерируем случайный MUID
random_muid = generate_random_muid()
print(f"\nСгенерирован случайный MUID: {random_muid}")

# Тип объекта (мультиселект)
results["Тип объекта"] = find_field_by_label("Тип объекта", exclude_select_all=True)
press_tab()

# MUID (текстовое поле)
results["MUID"] = find_field_by_label("MUID", action_type="input", value=random_muid)
press_tab()

# Адрес
results["Адрес"] = find_field_by_label("Адрес", action_type="address")
# Не нажимаем Tab после адреса

# АО (мультиселект)
results["АО"] = find_field_by_label("АО", exclude_select_all=True)
press_tab()

# Район (мультиселект)
results["Район"] = find_field_by_label("Район", exclude_select_all=True)
press_tab()

# Номер ТП (текстовое поле)
results["Номер ТП"] = find_field_by_label("Номер ТП", action_type="input", value="123")
press_tab()

# Филиал (мультиселект)
results["Филиал"] = find_field_by_label("Филиал", exclude_select_all=True)
press_tab()

# Предприятие (мультиселект)
results["Предприятие"] = find_field_by_label("Предприятие", exclude_select_all=True)
press_tab()

# Наличие ПУ (одиночный селект)
results["Наличие ПУ"] = find_field_by_label("Наличие ПУ", exclude_select_all=False)
press_tab()

# Номер ПУ (текстовое поле)
results["Номер ПУ"] = find_field_by_label("Номер ПУ", action_type="input", value="158")
press_tab()

# Марка ПУ (мультиселект)
results["Марка ПУ"] = find_field_by_label("Марка ПУ", exclude_select_all=True)
press_tab()

# ЦТП/ИТП (мультиселект)
results["ЦТП/ИТП"] = find_field_by_label("ЦТП/ИТП", exclude_select_all=True)
# Не нажимаем Tab после последнего поля

print("\nВсе поля обработаны")

# 7. СБРОС ФИЛЬТРОВ И ПРОВЕРКА ОЧИСТКИ
print("\n" + "=" * 50)
print("ШАГ 7: СБРОС ФИЛЬТРОВ И ПРОВЕРКА ОЧИСТКИ")
print("=" * 50)

reset_before_check = reset_filters()
#ожидание загрузки после сброса
load_duration = wait_for_page_load()


# Проверяем что все поля сбросились
not_emptied_fields = check_fields_emptiness()

if not_emptied_fields:
    print(f"\nВНИМАНИЕ! Найдены поля которые не сбросились ({len(not_emptied_fields)}):")
    for field_info in not_emptied_fields:
        print(f"  • {field_info}")
        add_error(f"Поле не сбросилось: {field_info}")
else:
    print("\nВсе поля успешно сброшены!")

# 8. ВЫБОР И ПРОВЕРКА АО
print("\n" + "=" * 50)
print("ШАГ 8: ВЫБОР И ПРОВЕРКА АО")
print("=" * 50)

print("\nВыбираем АО для проверки фильтрации...")
ao_selected = find_field_by_label("АО", exclude_select_all=True)

if ao_selected and selected_ao_value:
    print(f"\nВыбранное АО для проверки: '{selected_ao_value}'")

    if apply_filters():
        table_valid, row_count = check_table_for_ao(selected_ao_value)

        if table_valid and row_count > 0:
            print(f"\n✓ Таблица проверена успешно!")
            print(f"   • Найдено строк: {row_count}")
            print(f"   • Все строки соответствуют АО: '{selected_ao_value}'")
        else:
            if row_count == 0:
                add_error(f"Таблица пуста после применения фильтра с АО: '{selected_ao_value}'")
            else:
                add_error(f"Найдены строки не соответствующие выбранному АО: '{selected_ao_value}'")
    else:
        add_error("Не удалось применить фильтры")
else:
    add_error("Не удалось выбрать АО для проверки")

# 9. ФИНАЛЬНЫЙ СБРОС ФИЛЬТРОВ
print("\n" + "=" * 50)
print("ШАГ 9: ФИНАЛЬНЫЙ СБРОС ФИЛЬТРОВ")
print("=" * 50)

# Открываем фильтр если закрыт
click_svg_element(FILTER_SELECTOR, "Открыть фильтр")
time.sleep(1)

reset_final = reset_filters()
if reset_final:
    time.sleep(1)
    not_emptied_final = check_fields_emptiness()
    if not_emptied_final:
        print(f"\nВНИМАНИЕ! После финального сброса не сбросились ({len(not_emptied_final)}):")
        for field_info in not_emptied_final:
            print(f"  • {field_info}")
    else:
        print("\n✓ Все поля сброшены (финальная проверка)")

# 10. ОЖИДАНИЕ ЗАГРУЗКИ ПОСЛЕ СБРОСА
print("\n" + "=" * 50)
print("ШАГ 10: ОЖИДАНИЕ ЗАГРУЗКИ ДАННЫХ ПОСЛЕ СБРОСА")
print("=" * 50)

load_duration_after_reset = wait_for_page_load()

# 11. ФИНАЛЬНЫЙ ОТЧЕТ
print("\n" + "=" * 60)
print("ИТОГОВЫЙ ОТЧЕТ")
print("=" * 60)

print(f"\nРаздел: {section_name}")
print(f"URL: {section_url}")
print(f"Время загрузки после первого сброса: {load_duration:.1f} сек")
print(f"Время загрузки после финального сброса: {load_duration_after_reset:.1f} сек")

print(f"\nРезультаты обработки полей:")
for field_name, status in results.items():
    print(f"  {'✓' if status else '✗'} {field_name}")

# Вывод пропущенных полей
if skipped_fields:
    print(f"\nПропущенные поля ({len(skipped_fields)}):")
    for skipped in skipped_fields:
        print(f"  • {skipped['field']}: {skipped['reason']}")

if selected_ao_value:
    print(f"\nПроверка фильтрации по АО:")
    print(f"  Выбранное АО: '{selected_ao_value}'")
    if 'table_valid' in locals() and 'row_count' in locals():
        if table_valid and row_count > 0:
            print(f"  Статус: УСПЕШНО ✓")
            print(f"  Количество строк в таблице: {row_count}")
            print(f"  Все строки соответствуют выбранному АО")
        else:
            print(f"  Статус: ПРОВАЛЕН ✗")
            if row_count == 0:
                print(f"  Причина: Таблица пуста")
            else:
                print(f"  Причина: Найдены строки с другими АО")
    else:
        print(f"  Статус: ПРОВЕРКА НЕ ВЫПОЛНЕНА")

print(f"\nИтог проверки фильтрации:")
if section_errors:
    print(f"Найдено ошибок: {len(section_errors)}")
    print("\nСписок ошибок:")
    for i, error in enumerate(section_errors, 1):
        print(f"  {i}. {error}")
else:
    print(f"✓ Все шаги выполнены успешно!")
    print("  Раздел работает корректно")
    print("  Фильтрация по АО работает корректно")

print(f"\n{'=' * 60}")

# Закрытие браузера
try:
    print("Закрытие браузера...")
    driver.quit()
    print("Браузер успешно закрыт")
except Exception as e:
    print(f"Не удалось закрыть браузер: {e}")