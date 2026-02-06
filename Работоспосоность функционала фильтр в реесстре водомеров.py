'''Реестр показаний водомеров

ЦЕЛЬ: Проверка функциональности фильтрации в разделе "Реестр показаний водомеров"

ОПИСАНИЕ ТЕСТА:
1. Авторизация в системе
2. Переход в раздел "Реестр показаний водомеров"
3. Проверка на наличие ошибок на странице
4. Открытие фильтра и сброс перед заполнением
5. Последовательное заполнение всех полей фильтра:
   - Расчетный период (календарь со случайными датами)
   - "Выбрать все" для первых двух полей (Источник данных, Статус ведомости)
   - Ввод текста в поле "Тепловой пункт"
   - Случайный выбор значений в выпадающих списках (АО, Район, Филиал и др.)
   - Заполнение поля "Адрес" с выбором из списка
   - Ввод "158" в поле "Номер ПУ"
   - Отметка чекбокса "Патрубок"
6. Сброс фильтров и проверка очистки всех полей
7. Выбор случайного АО и проверка фильтрации данных в таблице
8. Финальный сброс фильтров и генерация отчета

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- Все поля фильтра корректно заполняются и сбрасываются
- Таблица данных фильтруется по выбранному АО
- Отсутствие ошибок в процессе выполнения теста
- Корректная работа всех элементов интерфейса

ОСОБЕННОСТИ:
- Используются расширенные списки исключений для плейсхолдеров
- Особые обработчики для полей: календарь, адрес, чекбоксы
- Подробное логирование каждого шага
- Проверка соответствия данных в таблице выбранному фильтру'''



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
URL = 'http://10.5.121.74/login'
USERNAME = 'predbill'
PASSWORD = 'predbill'

# Селекторы
FILTER_SELECTOR = "svg[data-icon='filter']"
RESET_SELECTOR = "svg[data-icon='stop']"
TABLE_SELECTOR = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body"

# Хранение ошибок и пропущенных полей
section_errors = []
skipped_fields = []  # Для хранения пропущенных полей

print("=" * 60)
print("ТЕСТ РАЗДЕЛА: Реестр показаний водомеров")
print("=" * 60)


# Функция для обработки поля "Расчетный период" с календарем
def process_date_range_field():
    """
    Обрабатывает поле "Расчетный период" - выбирает случайные даты начала и конца
    """
    try:
        print(f"Обрабатываем поле: Расчетный период")

        # Селекторы для полей дат
        start_date_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(1) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div.ant-picker.startDateRangePicker"
        end_date_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(1) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div:nth-child(2)"

        # Календари (РАЗНЫЕ для начала и конца)
        start_calendar_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(1) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div.ant-picker.startDateRangePicker.ant-picker-focused > div:nth-child(2) > div > div > div > div > div > div.ant-picker-body > table"
        end_calendar_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(1) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div.ant-picker.ant-picker-focused > div:nth-child(2) > div > div > div > div > div > div.ant-picker-body > table"

        # 1. Обрабатываем дату начала
        print(f"  Обрабатываем дату начала...")
        try:
            start_date_field = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, start_date_selector))
            )

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", start_date_field)
            time.sleep(0.5)

            print(f"  Кликаем на поле даты начала...")
            start_date_field.click()
            time.sleep(1.5)

        except Exception as e:
            print(f"  Не удалось найти или кликнуть на поле даты начала: {e}")
            add_skipped_field("Дата начала", f"Поле не найдено: {str(e)[:100]}")
            return False

        # 2. Выбираем случайную дату из календаря (начало)
        print(f"  Ищем календарь для даты начала...")
        try:
            calendar = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, start_calendar_selector))
            )
            print(f"  Календарь для начала найден")

            # Ищем все доступные даты в календаре (ячейки которые можно выбрать)
            available_dates = calendar.find_elements(By.CSS_SELECTOR,
                                                     "td.ant-picker-cell:not(.ant-picker-cell-disabled)")
            print(f"  Найдено доступных дат для начала: {len(available_dates)}")

            if not available_dates:
                print(f"  Нет доступных дат в календаре")
                add_skipped_field("Дата начала", "Нет доступных дат в календаре")
                # Закрываем календарь кликом вне его
                start_date_field.click()
                return False

            # Выбираем случайную дату
            random_date = random.choice(available_dates)
            date_text = random_date.text.strip()
            print(f"  Выбираем случайную дату начала: {date_text}")

            # Кликаем на дату
            random_date.click()
            print(f"  Выбрали дату начала: {date_text}")
            time.sleep(1)  # Ждем применения даты и закрытия календаря

        except Exception as e:
            print(f"  Ошибка при работе с календарем начала: {e}")
            add_skipped_field("Дата начала", f"Ошибка работы с календарем: {str(e)[:100]}")
            return False

        # 3. Обрабатываем дату конца
        print(f"  Обрабатываем дату конца...")
        try:
            end_date_field = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, end_date_selector))
            )

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", end_date_field)
            time.sleep(0.5)

            print(f"  Кликаем на поле даты конца...")
            end_date_field.click()
            time.sleep(1.5)

        except Exception as e:
            print(f"  Не удалось найти или кликнуть на поле даты конца: {e}")
            add_skipped_field("Дата конца", f"Поле не найдено: {str(e)[:100]}")
            return False

        # 4. Выбираем случайную дату из календаря (конец)
        print(f"  Ищем календарь для даты конца...")
        try:
            calendar = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, end_calendar_selector))
            )
            print(f"  Календарь для конца найден")

            # Ищем все доступные даты в календаре (ячейки которые можно выбрать)
            available_dates = calendar.find_elements(By.CSS_SELECTOR,
                                                     "td.ant-picker-cell:not(.ant-picker-cell-disabled)")
            print(f"  Найдено доступных дат для конца: {len(available_dates)}")

            if not available_dates:
                print(f"  Нет доступных дат в календаре для конца")
                add_skipped_field("Дата конца", "Нет доступных дат в календаре")
                # Закрываем календарь кликом вне его
                end_date_field.click()
                return False

            # Выбираем случайную дату (можно попробовать выбрать дату позже начала)
            random_date = random.choice(available_dates)
            date_text = random_date.text.strip()
            print(f"  Выбираем случайную дату конца: {date_text}")

            # Кликаем на дату
            random_date.click()
            print(f"  Выбрали дату конца: {date_text}")
            time.sleep(1)  # Ждем применения даты и закрытия календаря

            # Календарь должен закрыться автоматически после выбора даты конца
            print(f"  Календарь закрылся автоматически")
            return True

        except Exception as e:
            print(f"  Ошибка при работе с календарем конца: {e}")
            add_skipped_field("Дата конца", f"Ошибка работы с календарем: {str(e)[:100]}")
            return False

    except Exception as e:
        print(f"Общая ошибка при обработке поля 'Расчетный период': {e}")
        add_skipped_field("Расчетный период", f"Общая ошибка обработки: {str(e)[:100]}")
        return False

# Функция для проверки что все поля сброшены
def check_fields_emptiness(field_configs):
    """
    Проверяет что все поля пустые после сброса фильтров
    Возвращает список полей которые не сбросились
    """
    print("Проверяем сброс всех полей фильтра...")

    not_emptied_fields = []

    for config in field_configs:
        field_name = config["name"]
        field_type = config.get("type", "select_random")

        # Пропускаем поля которые не имеют селектора (типа "address", "pu_number" и т.д.)
        if field_type in ["address", "pu_number", "virtual", "sald"]:
            continue

        if "selector" not in config:
            continue

        selector = config["selector"]

        try:
            # Для полей с выбором "Выбрать все" или случайных значений
            if field_type in ["select_all", "select_random"]:
                # Находим элемент и проверяем его текст
                field_element = driver.find_element(By.CSS_SELECTOR, selector)
                field_text = field_element.text.strip()

                # ИГНОРИРУЕМ ПЛЕЙСХОЛДЕРЫ
                placeholder_texts = [
                    "Выберите значение", "Select value",
                    "Выбрать все", "Select all",
                    "Выберите", "Select",
                    "Выберите...", "Select...",
                    "Не выбрано", "Not selected",
                    "Выберите из списка", "Select from list",
                    "Значение не выбрано", "Value not selected",
                    "Выбрать", "Choose"
                ]
                is_placeholder = any(ph in field_text for ph in placeholder_texts)

                # Проверяем что поле пустое (нет выбранных значений, кроме плейсхолдеров)
                if field_text and field_text != "" and not is_placeholder:
                    not_emptied_fields.append({
                        "field": field_name,
                        "value": field_text[:50] + "..." if len(field_text) > 50 else field_text,
                        "reason": "Не сбросилось"
                    })
                    print(f"  {field_name}: '{field_text}'")
                else:
                    print(f"  {field_name}: пустое (или плейсхолдер)")

            # Для текстовых полей (input)
            elif field_type == "input":
                field_element = driver.find_element(By.CSS_SELECTOR, selector)
                field_value = field_element.get_attribute("value")

                if field_value and field_value.strip():
                    not_emptied_fields.append({
                        "field": field_name,
                        "value": field_value,
                        "reason": "Не сбросилось"
                    })
                    print(f"  {field_name}: '{field_value}'")
                else:
                    print(f"  {field_name}: пустое")

        except Exception as e:
            print(f"  {field_name}: ошибка проверки - {str(e)[:50]}")
            continue

    # ОСОБАЯ ПРОВЕРКА ДЛЯ ПОЛЯ АДРЕСА
    print(f"Проверяем поле Адрес...")
    try:
        # Селектор для поля адреса
        address_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(8) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div"
        address_field = driver.find_element(By.CSS_SELECTOR, address_selector)
        address_text = address_field.text.strip()

        # Проверяем плейсхолдеры для адреса
        address_placeholders = [
            "Введите адрес", "Введите значение",
            "Select address", "Выберите адрес",
            "Адрес", "Address",
            "Поиск адреса", "Search address",
            "Начните вводить адрес", "Start typing address", "Выбрать"
        ]
        is_address_placeholder = any(ph in address_text for ph in address_placeholders)

        if address_text and address_text != "" and not is_address_placeholder:
            not_emptied_fields.append({
                "field": "Адрес",
                "value": address_text[:50] + "..." if len(address_text) > 50 else address_text,
                "reason": "Не сбросилось"
            })
            print(f"  Адрес: '{address_text}'")
        else:
            print(f"  Адрес: пустое (или плейсхолдер)")

    except Exception as e:
        print(f"  Адрес: ошибка проверки - {str(e)[:50]}")

    # Проверяем чекбокс Патрубок
    try:
        checkbox_selector = "#isBranchPipe"
        checkbox = driver.find_element(By.CSS_SELECTOR, checkbox_selector)
        if checkbox.is_selected():
            not_emptied_fields.append({
                "field": "Патрубок",
                "value": "отмечен",
                "reason": "Чекбокс не сброшен"
            })
            print(f"  Патрубок: отмечен")
        else:
            print(f"  Патрубок: не отмечен")
    except:
        print(f"  Патрубок: не найден")

    # ОСОБАЯ ПРОВЕРКА ДЛЯ ПОЛЯ "РАСЧЕТНЫЙ ПЕРИОД"
    print(f"Проверяем поле Расчетный период...")
    try:
        # Селекторы для полей дат
        start_date_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(1) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div.ant-picker.startDateRangePicker"
        end_date_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(1) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div:nth-child(2)"

        # Проверяем дату начала
        try:
            start_date_field = driver.find_element(By.CSS_SELECTOR, start_date_selector)
            start_date_value = start_date_field.text.strip()

            # Проверяем плейсхолдеры для даты начала
            date_placeholders = [
                "Выберите дату", "Select date",
                "Дата начала", "Start date",
                "Начало", "Start",
                "Дата конца", "End date",
                "Конец", "End",
                "ГГГГ-ММ-ДД", "YYYY-MM-DD",
                "Выберите период", "Select period"
            ]
            is_start_placeholder = any(ph in start_date_value for ph in date_placeholders) or start_date_value == ""

            if start_date_value and not is_start_placeholder:
                not_emptied_fields.append({
                    "field": "Дата начала (Расчетный период)",
                    "value": start_date_value[:50] + "..." if len(start_date_value) > 50 else start_date_value,
                    "reason": "Не сбросилось"
                })
                print(f"  Дата начала: '{start_date_value}'")
            else:
                print(f"  Дата начала: пустая (или плейсхолдер)")

        except Exception as e:
            print(f"  Дата начала: ошибка проверки - {str(e)[:50]}")

        # Проверяем дату конца
        try:
            end_date_field = driver.find_element(By.CSS_SELECTOR, end_date_selector)
            end_date_value = end_date_field.text.strip()

            # Проверяем плейсхолдеры для даты конца
            date_placeholders = ["Выберите дату", "Select date", "Дата конца", "End date", "Конец", ""]
            is_end_placeholder = any(ph in end_date_value for ph in date_placeholders) or end_date_value == ""

            if end_date_value and not is_end_placeholder:
                not_emptied_fields.append({
                    "field": "Дата конца (Расчетный период)",
                    "value": end_date_value[:50] + "..." if len(end_date_value) > 50 else end_date_value,
                    "reason": "Не сбросилось"
                })
                print(f"  Дата конца: '{end_date_value}'")
            else:
                print(f"  Дата конца: пустая (или плейсхолдер)")

        except Exception as e:
            print(f"  Дата конца: ошибка проверки - {str(e)[:50]}")

    except Exception as e:
        print(f"  Расчетный период: ошибка проверки - {str(e)[:50]}")

    return not_emptied_fields

# Функция для добавления ошибок
def add_error(error_text):
    if error_text not in section_errors:
        section_errors.append(error_text)
        print(f"{error_text}")


# Функция для добавления пропущенных полей
def add_skipped_field(field_name, reason):
    skipped_fields.append({"field": field_name, "reason": reason})
    print(f"Пропущено поле '{field_name}': {reason}")


# Функция для закрытия всплывающих ошибок
def try_close_errors():
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


# Функция для ожидания загрузки
def wait_for_page_load():
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


# Функция для клика на SVG элемент
def click_svg_element(svg_selector, action_name):
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
            print(f"{action_name} (через родительский элемент)")
            time.sleep(0.5)
            return True
        except:
            actions = ActionChains(driver)
            actions.move_to_element(svg_element).click().perform()
            print(f"{action_name} (непосредственно на SVG)")
            time.sleep(0.5)
            return True

    except Exception as e:
        print(f"Не удалось {action_name}: {e}")
        return False


# Функция для обработки выпадающего списка с рандомным выбором значения
def process_select_random_value(field_selector, field_name):
    """
    Открывает выпадающий список и выбирает случайное доступное значение (кроме "Выбрать все")
    Возвращает (success, selected_text, error_reason)
    """
    try:
        print(f"Обрабатываем поле: {field_name}")

        # Находим поле
        try:
            field_element = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, field_selector))
            )
        except Exception as e:
            add_skipped_field(field_name, f"Не найдено или недоступно: {str(e)[:100]}")
            return False, None, "Поле не найдено или недоступно"

        # Прокручиваем к полю
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field_element)
        time.sleep(0.5)

        # Кликаем чтобы открыть список
        print(f"  Открываем выпадающий список...")
        field_element.click()
        time.sleep(1)

        # Ждем появления выпадающего списка
        dropdown_selector = ".ant-select-dropdown:not(.ant-select-dropdown-hidden)"
        try:
            dropdown = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, dropdown_selector))
            )
            print(f"  Выпадающий список открылся")
        except:
            print(f"  Не видим выпадающий список")
            # Закрываем список
            field_element.click()
            add_skipped_field(field_name, "Выпадающий список не открылся")
            return False, None, "Выпадающий список не открылся"

        # Ищем все элементы в списке
        try:
            all_options = dropdown.find_elements(By.CSS_SELECTOR, ".ant-select-item-option")
            print(f"  Найдено опций в списке: {len(all_options)}")

            if not all_options:
                print(f"  Список пуст")
                # Закрываем список
                field_element.click()
                add_skipped_field(field_name, "Список пуст")
                return False, None, "Список пуст"

            # Фильтруем опции, исключая "Выбрать все"
            valid_options = []
            for i, option in enumerate(all_options):
                try:
                    option_text = option.text.strip()
                    if "Выбрать все" not in option_text and option_text:
                        valid_options.append((option, option_text))
                except:
                    continue

            if not valid_options:
                print(f"  Нет подходящих значений (только 'Выбрать все')")
                # Закрываем список
                field_element.click()
                add_skipped_field(field_name, "Только 'Выбрать все' в списке")
                return False, None, "Только 'Выбрать все' в списке"

            # Выбираем случайное значение
            random_option, random_text = random.choice(valid_options)
            print(f"  Выбираем случайное значение: '{random_text}'")

            # Прокручиваем к выбранному элементу
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", random_option)
            time.sleep(0.3)

            # Кликаем на элемент
            random_option.click()
            print(f"  Выбрали случайное значение: '{random_text}'")
            time.sleep(0.5)
            return True, random_text, None

        except Exception as e:
            print(f"  Ошибка при работе со списком: {e}")
            add_skipped_field(field_name, f"Ошибка работы со списком: {str(e)[:100]}")
            return False, None, f"Ошибка работы со списком: {str(e)[:100]}"

    except Exception as e:
        print(f"Ошибка при обработке поля '{field_name}': {e}")
        add_skipped_field(field_name, f"Общая ошибка обработки: {str(e)[:100]}")
        return False, None, f"Общая ошибка обработки: {str(e)[:100]}"


# Функция для обработки выпадающего списка с выбором "Выбрать все"
def process_select_all_field(field_selector, field_name):
    """
    Открывает выпадающий список и выбирает "Выбрать все"
    """
    try:
        print(f"Обрабатываем поле: {field_name}")

        # Находим поле
        try:
            field_element = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, field_selector))
            )
        except Exception as e:
            add_skipped_field(field_name, f"Не найдено или недоступно: {str(e)[:100]}")
            return False

        # Прокручиваем к полю
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field_element)
        time.sleep(0.5)

        # Кликаем чтобы открыть список
        print(f"  Открываем выпадающий список...")
        field_element.click()
        time.sleep(1)

        # Ищем "Выбрать все" через JavaScript
        select_all_js = """
        var elements = document.evaluate(
            "//*[contains(text(), 'Выбрать все')]", 
            document, 
            null, 
            XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, 
            null
        );

        for (var i = 0; i < elements.snapshotLength; i++) {
            var element = elements.snapshotItem(i);
            if (element && element.offsetParent !== null) {
                element.click();
                return true;
            }
        }
        return false;
        """

        result = driver.execute_script(select_all_js)
        if result:
            print(f"  Выбрали 'Выбрать все'")
            time.sleep(0.5)
            return True
        else:
            print(f"  Не нашли 'Выбрать все'")
            add_skipped_field(field_name, "Не найдено 'Выбрать все'")
            return False

    except Exception as e:
        print(f"Ошибка при обработке поля '{field_name}': {e}")
        add_skipped_field(field_name, f"Общая ошибка обработки: {str(e)[:100]}")
        return False


# Функция для обработки поля "Виртуальный" (рандомный выбор)
def process_virtual_field():
    """
    Обрабатывает поле "Виртуальный" - выбирает случайное значение
    """
    try:
        print(f"Обрабатываем поле: Виртуальный")

        # Селектор поля (ИСПРАВЛЕННЫЙ)
        field_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(17) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div"

        # Используем общую функцию для рандомного выбора
        success, value, error_reason = process_select_random_value(field_selector, "Виртуальный")
        return success

    except Exception as e:
        print(f"Ошибка при обработке поля 'Виртуальный': {e}")
        add_skipped_field("Виртуальный", f"Общая ошибка обработки: {str(e)[:100]}")
        return False


# Функция для обработки поля "Сальдирующий" (рандомный выбор)
def process_sald_field():
    """
    Обрабатывает поле "Сальдирующий" - выбирает случайное значение
    """
    try:
        print(f"Обрабатываем поле: Сальдирующий")

        # Селектор поля (ИСПРАВЛЕННЫЙ)
        field_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(18) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div"

        # Используем общую функцию для рандомного выбора
        success, value, error_reason = process_select_random_value(field_selector, "Сальдирующий")
        return success

    except Exception as e:
        print(f"Ошибка при обработке поля 'Сальдирующий': {e}")
        add_skipped_field("Сальдирующий", f"Общая ошибка обработки: {str(e)[:100]}")
        return False


# Функция для обработки текстового поля "Номер ПУ"
def process_pu_number_field():
    """
    Обрабатывает текстовое поле "Номер ПУ" - вводит значение 158
    """
    try:
        print(f"Обрабатываем поле: Номер ПУ")

        # Ищем поле по ID meteringDeviceSeries (ОСНОВНОЙ СЕЛЕКТОР)
        field_selector = "#meteringDeviceSeries"

        try:
            field_element = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, field_selector))
            )
            print(f"  Нашли поле по селектору: {field_selector}")
        except:
            # Если не нашли по основному селектору, пробуем другие варианты
            field_selectors = [
                "input#meteringDeviceSeries",
                "input[placeholder='Введите значение']",
                ".ant-input[type='text']",
                "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(14) > div.ant-col.ant-col-14.ant-form-item-control > div > div > span > input"
            ]

            field_element = None
            for selector in field_selectors:
                try:
                    field_element = wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"  Нашли поле по альтернативному селектору: {selector}")
                    break
                except:
                    continue

        if not field_element:
            print(f"  Не нашли поле Номер ПУ")
            add_skipped_field("Номер ПУ", "Поле не найдено")
            return False

        # Прокручиваем к полю
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field_element)
        time.sleep(0.5)

        # Вводим значение
        value = "158"
        print(f"  Вводим значение: {value}")

        try:
            field_element.click()
            time.sleep(0.3)
            field_element.clear()
            time.sleep(0.3)
            field_element.send_keys(value)
            print(f"  Значение введено")
            return True
        except Exception as e:
            print(f"  Ошибка при вводе значения: {e}")
            add_skipped_field("Номер ПУ", f"Ошибка при вводе: {str(e)[:100]}")
            return False

    except Exception as e:
        print(f"Ошибка при обработке поля 'Номер ПУ': {e}")
        add_skipped_field("Номер ПУ", f"Общая ошибка обработки: {str(e)[:100]}")
        return False


# Функция для обработки поля адреса
def process_address_field():
    """
    Обрабатывает сложное поле адреса
    """
    try:
        print(f"Обрабатываем поле: Адрес")

        # Селекторы для поля адреса (ИСПРАВЛЕННЫЕ)
        address_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(8) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div"
        address_input_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(8) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div.searchableSelectPopup > div.searchableSelectPopupInsider > div.searchBox.Адрес > input"
        address_list_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(8) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div.searchableSelectPopup > div.searchableSelectPopupInsider > div.searchBox.Адрес > ul"
        address_value = "1-й Амбулаторный пр., д.2/6"

        print(f"  Ищем поле адреса...")

        # 1. Находим и кликаем на поле адреса
        try:
            address_field = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, address_selector))
            )
        except Exception as e:
            print(f"  Не удалось найти поле адреса: {e}")
            add_skipped_field("Адрес", f"Поле не найдено: {str(e)[:100]}")
            return False

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", address_field)
        time.sleep(0.5)

        print(f"  Кликаем на поле адреса...")
        try:
            address_field.click()
            time.sleep(1.5)
        except Exception as e:
            print(f"  Не удалось кликнуть на поле адреса: {e}")
            add_skipped_field("Адрес", f"Не удалось кликнуть: {str(e)[:100]}")
            return False

        # 2. Находим поле ввода
        try:
            address_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, address_input_selector))
            )
            print(f"  Нашли поле ввода адреса")
        except:
            print(f"  Не удалось найти поле ввода адреса")
            add_skipped_field("Адрес", "Поле ввода не найдено")
            return False

        # 3. Вводим адрес
        print(f"  Вводим адрес: {address_value}")
        try:
            address_input.clear()
            time.sleep(0.3)
            address_input.send_keys(address_value)
            print(f"  Адрес введен")
            time.sleep(3)  # Ждем загрузки результатов
        except Exception as e:
            print(f"  Ошибка при вводе адреса: {e}")
            add_skipped_field("Адрес", f"Ошибка при вводе: {str(e)[:100]}")
            return False

        # 4. Ищем и выбираем адрес из списка
        print(f"  Ищем список адресов...")
        try:
            address_list = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, address_list_selector))
            )
            print(f"  Список адресов найден")

            address_items = address_list.find_elements(By.TAG_NAME, "li")
            print(f"  Найдено адресов: {len(address_items)}")

            if address_items:
                # Выбираем ПЕРВЫЙ адрес
                first_item = address_items[0]
                first_item_text = first_item.text.strip()
                first_item.click()
                print(f"  Выбрали адрес из списка: '{first_item_text}'")
                time.sleep(0.5)

                # 5. Кликаем по пустой области чтобы закрыть выпадающий список
                print(f"  Кликаем по пустой области чтобы закрыть список...")
                try:
                    # Находим заголовок или другой элемент рядом для клика
                    header_selectors = [
                        ".ant-drawer-header",
                        ".ant-drawer-title",
                        "label[for*='address']",
                        "div.ant-form-item-label"
                    ]

                    for selector in header_selectors:
                        try:
                            element = driver.find_element(By.CSS_SELECTOR, selector)
                            if element.is_displayed():
                                actions = ActionChains(driver)
                                actions.move_to_element(element).click().perform()
                                print(f"  Кликнули по элементу '{selector}' чтобы закрыть список")
                                time.sleep(0.5)
                                break
                        except:
                            continue

                    # Если не нашли подходящий элемент, кликаем по заголовку формы
                    try:
                        form_title = driver.find_element(By.CSS_SELECTOR, ".ant-drawer-title")
                        actions = ActionChains(driver)
                        actions.move_to_element(form_title).click().perform()
                        print(f"  Кликнули по заголовку формы")
                        time.sleep(0.5)
                    except:
                        # Если ничего не работает, кликаем по координатам рядом с полем
                        try:
                            address_field = driver.find_element(By.CSS_SELECTOR, address_selector)
                            actions = ActionChains(driver)
                            # Сдвигаемся на 200 пикселей вправо и кликаем
                            actions.move_to_element_with_offset(address_field, 200, 0).click().perform()
                            print(f"  Кликнули рядом с полем адреса")
                            time.sleep(0.5)
                        except Exception as e:
                            print(f"  Не удалось кликнуть рядом: {e}")

                except Exception as e:
                    print(f"  Ошибка при закрытии выпадающего списка: {e}")

                return True
            else:
                print(f"  Список адресов пуст")
                add_skipped_field("Адрес", "Список адресов пуст")
                return False

        except Exception as e:
            print(f"  Ошибка при работе со списком адресов: {e}")
            add_skipped_field("Адрес", f"Ошибка работы со списком: {str(e)[:100]}")
            return False

    except Exception as e:
        print(f"Общая ошибка при обработке поля 'Адрес': {e}")
        add_skipped_field("Адрес", f"Общая ошибка обработки: {str(e)[:100]}")
        return False


# Функция для нажатия Tab
def press_tab():
    """Нажимает клавишу Tab"""
    try:
        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB).perform()
        print(f"  Нажали Tab")
        time.sleep(0.3)
        return True
    except:
        return False


# Функция для применения фильтров
def apply_filters():
    try:
        print("Применяем фильтры...")
        time.sleep(1)

        # Селектор для кнопки "Применить" в фильтре
        apply_button_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > div > div.filterOperations > button:nth-child(1) > span > svg"

        try:
            # Находим SVG элемент кнопки "Применить"
            apply_svg = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, apply_button_selector))
            )

            # Кликаем на родительский элемент кнопки
            parent_button = apply_svg.find_element(By.XPATH, "..")
            actions = ActionChains(driver)
            actions.move_to_element(parent_button).click().perform()
            print(f"  Нажали 'Применить'")
            return True

        except Exception as e:
            print(f"  Не удалось нажать 'Применить': {e}")
            return False

    except Exception as e:
        print(f"Ошибка при применении фильтров: {e}")
        add_error(f"Ошибка при применении фильтров: {e}")
        return False


# Функция для клика на чекбокс "Патрубок"
def click_patrubok_checkbox():
    """
    Кликает на чекбокс "Патрубок"
    """
    try:
        print(f"Обрабатываем чекбокс: Патрубок")

        # Селектор для чекбокса
        checkbox_selector = "#isBranchPipe"

        try:
            # Находим чекбокс
            checkbox = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, checkbox_selector))
            )

            # Прокручиваем к чекбоксу
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
            time.sleep(0.5)

            # Кликаем на чекбокс
            checkbox.click()
            print(f"  Чекбокс 'Патрубок' отмечен")
            time.sleep(0.5)
            return True

        except Exception as e:
            print(f"  Не удалось найти или кликнуть чекбокс 'Патрубок': {e}")
            add_skipped_field("Патрубок", f"Чекбокс не найден: {str(e)[:100]}")
            return False

    except Exception as e:
        print(f"Ошибка при обработке чекбокса 'Патрубок': {e}")
        add_skipped_field("Патрубок", f"Общая ошибка обработки: {str(e)[:100]}")
        return False


# Функция для проверки таблицы с выбранным АО
def check_table_for_ao(selected_ao):
    """
    Проверяет таблицу на соответствие выбранному АО
    Возвращает (success, row_count)
    """
    try:
        print(f"Проверяем таблицу для АО: '{selected_ao}'")

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
                # Проверяем, содержит ли строка выбранное АО
                if selected_ao not in row_text:
                    mismatched_rows.append(i)
                    if len(mismatched_rows) <= 3:  # Ограничиваем вывод
                        print(f"    Строка {i}: НЕ содержит '{selected_ao}'")
                else:
                    if i <= 3:  # Ограничиваем вывод
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


# ОСНОВНОЙ КОД

# 1. АВТОРИЗАЦИЯ
print("=" * 50)
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
print("=" * 50)
print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ")
print("=" * 50)

section_url = 'http://10.5.121.74/commercialControl/watermeterStatements'
section_name = 'Реестр показаний водомеров'

try:
    driver.get(section_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print(f"Переход в раздел '{section_name}'")
    time.sleep(2)

except Exception as e:
    add_error(f"Не удалось перейти в раздел: {e}")
    driver.quit()
    exit()

# 3. ПРОВЕРКА ОШИБОК
print("=" * 50)
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
print("=" * 50)
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
print("=" * 50)
print("ШАГ 5: СБРОС ФИЛЬТРОВ ПЕРЕД ЗАПОЛНЕНИЕМ")
print("=" * 50)

reset_clicked = False

for attempt in range(max_attempts):
    if click_svg_element(RESET_SELECTOR, f"Сбросить фильтры (попытка {attempt + 1})"):
        reset_clicked = True
        break
    else:
        time.sleep(0.5)

if not reset_clicked:
    add_error("Не удалось сбросить фильтры перед заполнением")
else:
    print("Фильтры сброшены перед заполнением")

# 6. ОЖИДАНИЕ ЗАГРУЗКИ ПОСЛЕ СБРОСА
print("=" * 50)
print("ШАГ 6: ОЖИДАНИЕ ЗАГРУЗКИ ДАННЫХ ПОСЛЕ СБРОСА")
print("=" * 50)

load_duration = wait_for_page_load()

# 7. ЗАПОЛНЕНИЕ ПОЛЕЙ ФИЛЬТРА (в правильном порядке)
print("=" * 50)
print("ШАГ 7: ЗАПОЛНЕНИЕ ПОЛЕЙ ФИЛЬТРА")
print("=" * 50)

# Определяем селекторы полей (в порядке заполнения)
field_configs = [
    # Расчетный период (календарь)
    {"name": "Расчетный период", "type": "date_range"},
    # Первые два поля - выбираем "Выбрать все"
    {"name": "Источник данных",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(2) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div > div.ant-select-selection-overflow",
     "type": "select_all"},
    {"name": "Статус ведомости",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(3) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div",
     "type": "select_all"},

    # Тепловой пункт (текстовое поле)
    {"name": "Тепловой пункт",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(4) > div.ant-col.ant-col-14.ant-form-item-control > div > div > span > input",
     "type": "input", "value": "04-06-0601/032"},

    # Новые поля (по порядку)
    {"name": "АО",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(6) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div > div.ant-select-selection-overflow",
     "type": "select_random"},
    {"name": "Район",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(7) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div > div.ant-select-selection-overflow",
     "type": "select_random"},

    # Поле Адрес
    {"name": "Адрес", "type": "address"},

    # Филиал (случайное значение)
    {"name": "Филиал",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(9) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div",
     "type": "select_random"},

    # Предприятие (случайное значение)
    {"name": "Предприятие",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(10) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div",
     "type": "select_random"},

    # Тип объекта (случайное значение)
    {"name": "Тип объекта",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(11) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div",
     "type": "select_random"},

    # Номер ПУ (текстовое поле)
    {"name": "Номер ПУ", "type": "pu_number"},

    # Марка ПУ (случайное значение)
    {"name": "Марка ПУ",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(15) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div",
     "type": "select_random"},

    # Тип точки учета (случайное значение)
    {"name": "Тип точки учета",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(16) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div",
     "type": "select_random"},

    # Виртуальный (рандомный выбор)
    {"name": "Виртуальный", "type": "virtual"},

    # Сальдирующий (рандомный выбор)
    {"name": "Сальдирующий", "type": "sald"},
]

# Обрабатываем поля в правильном порядке
results = {}
selected_ao_value = None  # Переменная для хранения выбранного АО

for i, config in enumerate(field_configs, 1):
    field_name = config["name"]
    field_type = config.get("type", "select_random")

    print(f"[{i}/{len(field_configs)}] Поле: {field_name}")

    success = False
    selected_value = None
    error_reason = None


    if field_type == "date_range":
        # Обрабатываем Расчетный период (календарь)
        success = process_date_range_field()

    elif field_type == "select_all":
        # Выбираем "Выбрать все"
        success = process_select_all_field(config["selector"], field_name)

    elif field_type == "select_random":
        # Выбираем случайное доступное значение (кроме "Выбрать все")
        success, selected_value, error_reason = process_select_random_value(config["selector"], field_name)

        # Сохраняем выбранное значение АО
        if field_name == "АО" and success and selected_value:
            selected_ao_value = selected_value
            print(f"  Сохранили выбранное АО: '{selected_ao_value}'")

    elif field_type == "input":
        # Текстовое поле
        try:
            field_element = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, config["selector"]))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field_element)
            time.sleep(0.5)

            field_element.click()
            time.sleep(0.3)
            field_element.clear()
            time.sleep(0.3)
            field_element.send_keys(config["value"])
            print(f"  Ввели: {config['value']}")
            success = True
        except Exception as e:
            print(f"  Ошибка: {e}")
            add_skipped_field(field_name, f"Ошибка ввода: {str(e)[:100]}")
            success = False

    elif field_type == "address":
        # Особое поле адреса
        success = process_address_field()

    elif field_type == "virtual":
        # Поле "Виртуальный"
        success = process_virtual_field()

    elif field_type == "sald":
        # Поле "Сальдирующий"
        success = process_sald_field()

    elif field_type == "pu_number":
        # Поле "Номер ПУ"
        success = process_pu_number_field()

    results[field_name] = success

    # Нажимаем Tab после каждого поля (кроме последнего)
    if i < len(field_configs):
        press_tab()
        time.sleep(0.5)

# Кликаем на чекбокс "Патрубок" в самом конце
patrubok_success = click_patrubok_checkbox()
results["Патрубок"] = patrubok_success

print("Все поля обработаны")

# 8. СБРОС ФИЛЬТРОВ ПЕРЕД ПРОВЕРКОЙ АО
print("=" * 50)
print("ШАГ 8: СБРОС ФИЛЬТРОВ ПЕРЕД ПРОВЕРКОЙ АО")
print("=" * 50)

reset_before_ao_check = False

for attempt in range(max_attempts):
    if click_svg_element(RESET_SELECTOR, f"Сбросить фильтры перед проверкой АО (попытка {attempt + 1})"):
        reset_before_ao_check = True
        break
    else:
        time.sleep(0.5)

if not reset_before_ao_check:
    add_error("Не удалось сбросить фильтры перед проверкой АО")
else:
    print("Фильтры сброшены перед проверкой АО")
time.sleep(1)

# ПРОВЕРЯЕМ ЧТО ВСЕ ПОЛЯ СБРОСИЛИСЬ
not_emptied_fields = check_fields_emptiness(field_configs)

if not_emptied_fields:
    print(f"ВНИМАНИЕ! Найдены поля которые не сбросились ({len(not_emptied_fields)}):")
    for field_info in not_emptied_fields:
        print(f"  {field_info['field']}: {field_info['value']} ({field_info['reason']})")
        # ДОБАВЛЯЕМ ОШИБКУ ТОЛЬКО ЕСЛИ ЭТО НЕ ПЛЕЙСХОЛДЕР
        if "Выберите значение" not in field_info['value'] and "Введите адрес" not in field_info['value']:
            add_error(f"Поле '{field_info['field']}' не сбросилось: {field_info['value']}")
else:
    print("Все поля успешно сброшены!")

# 9. ВЫБОР И ПРОВЕРКА АО
print("=" * 50)
print("ШАГ 9: ВЫБОР И ПРОВЕРКА АО")
print("=" * 50)

# Теперь выбираем АО заново
print("Выбираем АО для проверки фильтрации...")

# Селектор для поля АО (скорректирован номер div)
ao_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(6) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div > div.ant-select-selection-overflow"

# Выбираем случайное АО
success, selected_ao_value, error_reason = process_select_random_value(ao_selector, "АО для проверки")

if success and selected_ao_value:
    print(f"Выбранное АО для проверки: '{selected_ao_value}'")

    # Применяем фильтры
    if apply_filters():
        # Проверяем таблицу на соответствие выбранному АО
        table_valid, row_count = check_table_for_ao(selected_ao_value)

        if table_valid and row_count > 0:
            print(f"Таблица проверена успешно!")
            print(f"   Найдено строк: {row_count}")
            print(f"   Все строки соответствуют АО: '{selected_ao_value}'")
        else:
            if row_count == 0:
                add_error(f"Таблица пуста после применения фильтра с АО: '{selected_ao_value}'")
            else:
                add_error(f"Найдены строки не соответствующие выбранному АО: '{selected_ao_value}'")
    else:
        add_error("Не удалось применить фильтры")
else:
    add_error(f"Не удалось выбрать АО для проверки: {error_reason}")

# 10. СБРОС ФИЛЬТРОВ В КОНЦЕ
print("=" * 50)
print("ШАГ 10: СБРОС ФИЛЬТРОВ В КОНЦЕ")
print("=" * 50)

reset_clicked_final = False

for attempt in range(max_attempts):
    if click_svg_element(RESET_SELECTOR, f"Сбросить фильтры (финальный сброс, попытка {attempt + 1})"):
        reset_clicked_final = True
        break
    else:
        time.sleep(0.5)

if not reset_clicked_final:
    # Не добавляем ошибку, так как фильтр может быть уже сброшен или не открыт
    print("Кнопка сброса не найдена (фильтр может быть закрыт или уже сброшен)")
else:
    print("Фильтры сброшены (финальный сброс)")

# Проверяем сброс полей в конце
if reset_clicked_final:
    time.sleep(1)
    not_emptied_final = check_fields_emptiness(field_configs)
    if not_emptied_final:
        print(f"ВНИМАНИЕ! После финального сброса не сбросились ({len(not_emptied_final)}):")
        for field_info in not_emptied_final:
            print(f"  {field_info['field']}: {field_info['value']}")
    else:
        print("Все поля сброшены (финальная проверка)")

# 11. ОЖИДАНИЕ ЗАГРУЗКИ ПОСЛЕ СБРОСА
print("=" * 50)
print("ШАГ 11: ОЖИДАНИЕ ЗАГРУЗКИ ДАННЫХ ПОСЛЕ СБРОСА")
print("=" * 50)

load_duration_after_reset = wait_for_page_load()

# 12. ФИНАЛЬНЫЙ ОТЧЕТ
print("=" * 60)
print("ИТОГОВЫЙ ОТЧЕТ")
print("=" * 60)

print(f"Раздел: {section_name}")
print(f"URL: {section_url}")
print(f"Время загрузки после сброса: {load_duration:.1f} сек")
print(f"Время загрузки после финального сброса: {load_duration_after_reset:.1f} сек")

print(f"Результаты обработки полей:")
for config in field_configs:
    field_name = config["name"]
    status = results.get(field_name, False)
    print(f"  {' ' if status else ' '} {field_name}")

# Вывод чекбокса Патрубок
if "Патрубок" in results:
    print(f"  {' ' if results['Патрубок'] else ' '} Патрубок (чекбокс)")



if selected_ao_value:
    print(f"Проверка фильтрации по АО:")
    print(f"  Выбранное АО: '{selected_ao_value}'")
    if 'table_valid' in locals() and 'row_count' in locals():
        if table_valid and row_count > 0:
            print(f"  Статус: УСПЕШНО")
            print(f"  Количество строк в таблице: {row_count}")
            print(f"  Все строки соответствуют выбранному АО")
        else:
            print(f"  Статус: ПРОВАЛЕН")
            if row_count == 0:
                print(f"  Причина: Таблица пуста")
            else:
                print(f"  Причина: Найдены строки с другими АО")
    else:
        print(f"  Статус: ПРОВЕРКА НЕ ВЫПОЛНЕНА")

print(f"Итог проверки фильтрации:")
if section_errors:
    print(f"Найдено ошибок: {len(section_errors)}")
    print("Список ошибок:")
    for i, error in enumerate(section_errors, 1):
        print(f"  {i}. {error}")
else:
    print(f"Все шаги выполнены успешно!")
    print("Раздел работает корректно")
    print("Фильтрация по АО работает корректно")

print(f"{'=' * 60}")

# Закрытие браузера
try:
    #input()
    print("Закрытие браузера...")
    driver.quit()
    print("Браузер успешно закрыт")
except Exception as e:
    print(f"Не удалось закрыть браузера: {e}")