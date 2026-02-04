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
URL = 'http://10.5.121.74/login'
USERNAME = 'predbill'
PASSWORD = 'predbill'

# Селекторы
FILTER_SELECTOR = "svg[data-icon='filter']"
RESET_SELECTOR = "svg[data-icon='stop']"
APPLY_SELECTOR = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > div > div.filterOperations > button:nth-child(1) > span > svg"
SEARCH_INPUT_SELECTOR = "#root > section > section > div > div.mib-profile-control > div.mib-header-right-extra > div > div:nth-child(2) > form > div > div > span > span > span.ant-input-affix-wrapper"
SEARCH_CLEAR_SELECTOR = "#root > section > section > div > div.mib-profile-control > div.mib-header-right-extra > div > div:nth-child(2) > form > div > div > span > span > span.ant-input-affix-wrapper > span > span > span > svg > path"
SEARCH_TYPE_SELECTOR = "#root > section > section > div > div.mib-profile-control > div.mib-header-right-extra > div > div:nth-child(1) > form > div > div.ant-col.ant-form-item-control > div > div > div > div > span.ant-select-selection-item"
TABLE_SELECTOR = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body"
TABLE_HEADER_SELECTOR = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__header"

# Селекторы для шестеренки (настройки столбцов)
SETTINGS_GEAR_SELECTOR = "#root > section > section > div > div.mib-profile-control > div.mib-header-right-extra > div > div:nth-child(3) > button > span > svg"
SETTINGS_POPUP_SELECTOR = "body > div:nth-child(3) > div > div > div > div.ant-popover-inner"
SETTINGS_CONTENT_ROWS_SELECTOR = "body > div:nth-child(3) > div > div > div > div.ant-popover-inner > div.ant-popover-inner-content > div > div.user-config-editor-content-rows"
SETTINGS_SAVE_BUTTON_SELECTOR = "body > div:nth-child(3) > div > div > div > div.ant-popover-inner > div.ant-popover-inner-content > div > div.user-config-editor-content-footer > button.ant-btn.ant-btn-primary.ant-btn-sm > span"
SETTINGS_RESET_BUTTON_SELECTOR = "body > div:nth-child(3) > div > div > div > div.ant-popover-inner > div.ant-popover-title > div > button > span"
SETTINGS_CANCEL_BUTTON_SELECTOR = "body > div:nth-child(3) > div > div > div > div.ant-popover-inner > div.ant-popover-inner-content > div > div.user-config-editor-content-footer > button.ant-btn.ant-btn-link.ant-btn-sm > span"

# Базовый селектор для чекбоксов в шестеренке
CHECKBOX_BASE_SELECTOR = "body > div:nth-child(3) > div > div > div > div.ant-popover-inner > div.ant-popover-inner-content > div > div.user-config-editor-content-rows > div:nth-child({}) > div > label > span > input"

# Данные для поиска
SEARCH_TESTS = [
    {
        "name": "ПОИСК ПО АДРЕСУ",
        "type": "По адресу",
        "value": "1-й Амбулаторный пр., д.2/6",
        "column": "Адрес"
    },
    {
        "name": "ПОИСК ПО НОМЕРУ ПУ",
        "type": "Номеру ПУ",
        "value": "666",
        "column": "Номер ПУ"
    },
    {
        "name": "ПОИСК ПО НОМЕРУ ТП",
        "type": "Номеру ТП",
        "value": "02-04-1216/101",
        "column": "Тепловой пункт"
    }
]


def wait_for_page_load():
    """
    Ожидание загрузки данных на странице
    Возвращает время загрузки в секундах
    """
    print("⏳ Ожидание загрузки данных...")
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
        print(f"✓ Загрузка данных завершена за {load_duration:.1f} секунд")
        return load_duration

    except Exception as e:
        print(f"  ⚠ Ошибка при ожидании загрузки: {e}")
        return time.time() - load_start


def perform_search(search_value, search_type="По адресу"):
    """
    Выполняет поиск по указанному значению и типу
    """
    print(f"\n🔍 Выполняем поиск: тип='{search_type}', значение='{search_value}'")

    # Если нужно изменить тип поиска
    if search_type != "По адресу":
        try:
            print(f"  ↪ Меняем тип поиска на '{search_type}'...")
            search_type_element = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, SEARCH_TYPE_SELECTOR))
            )
            search_type_element.click()
            time.sleep(1)

            # Ищем нужный вариант в выпадающем списке
            dropdown_selector = ".ant-select-dropdown:not(.ant-select-dropdown-hidden)"
            dropdown = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, dropdown_selector))
            )

            # Ищем все опции
            options = dropdown.find_elements(By.CSS_SELECTOR, ".ant-select-item-option")
            option_found = False

            for option in options:
                try:
                    option_text = option.text.strip()
                    if search_type in option_text:
                        option.click()
                        print(f"  ✓ Выбран тип поиска: '{search_type}'")
                        option_found = True
                        time.sleep(1)
                        break
                except:
                    continue

            if not option_found:
                print(f"  ⚠ Не найден тип поиска '{search_type}', используем текущий")

        except Exception as e:
            print(f"  ⚠ Ошибка при смене типа поиска: {e}")

    # Выполняем поиск
    try:
        # Находим поле поиска
        search_input = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, SEARCH_INPUT_SELECTOR))
        )

        # Кликаем на поле поиска
        search_input.click()
        time.sleep(0.5)

        # Находим input внутри wrapper
        try:
            input_element = search_input.find_element(By.TAG_NAME, "input")
        except:
            input_element = search_input

        # Вводим значение
        input_element.clear()
        time.sleep(0.3)
        input_element.send_keys(search_value)
        time.sleep(0.5)

        # Нажимаем Enter
        input_element.send_keys(Keys.ENTER)
        print("✓ Поиск выполнен")
        return True

    except Exception as e:
        print(f"✗ Ошибка при выполнении поиска: {e}")
        return False


def clear_search():
    """
    Очищает поле поиска нажатием на крестик
    """
    print("\n🧹 Очищаем поле поиска...")

    try:
        # Находим крестик для очистки
        clear_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, SEARCH_CLEAR_SELECTOR))
        )

        # Нажимаем на крестик (может потребоваться клик по родительскому элементу)
        try:
            clear_button.click()
        except:
            # Пробуем кликнуть по родительскому элементу
            parent = clear_button.find_element(By.XPATH, "..")
            parent.click()

        print("✓ Поле поиска очищено")
        return True

    except Exception as e:
        print(f"✗ Не удалось очистить поле поиска: {e}")
        return False


def check_table_for_value(search_value, expected_column=None):
    """
    Проверяет таблицу на наличие указанного значения
    Возвращает (success, total_rows, mismatched_rows)
    """
    print(f"\n📊 Проверяем таблицу на наличие значения: '{search_value}'")

    try:
        # Ждем загрузки таблицы
        table_body = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, TABLE_SELECTOR))
        )

        # Получаем все строки таблицы
        rows = table_body.find_elements(By.CSS_SELECTOR, ".BaseTable__row")

        if not rows:
            print("⚠ Таблица пуста после поиска")
            return False, 0, []

        print(f"📊 Найдено строк в таблице: {len(rows)}")

        # Определяем индекс столбца если указан expected_column
        column_index = None
        if expected_column:
            try:
                header = driver.find_element(By.CSS_SELECTOR, TABLE_HEADER_SELECTOR)
                header_cells = header.find_elements(By.CSS_SELECTOR, ".BaseTable__header-cell")

                for i, cell in enumerate(header_cells):
                    cell_text = cell.text.strip()
                    if expected_column in cell_text:
                        column_index = i
                        print(f"🔍 Найден столбец '{expected_column}' с индексом: {i}")
                        break

                if column_index is None:
                    print(f"⚠ Не найден столбец '{expected_column}', проверяем все строки")
            except:
                print("⚠ Не удалось определить индекс столбца")

        # Проверяем каждую строку
        mismatched_rows = []

        for i, row in enumerate(rows, 1):
            try:
                if column_index is not None:
                    # Проверяем конкретный столбец
                    cells = row.find_elements(By.CSS_SELECTOR, ".BaseTable__row-cell")
                    if len(cells) > column_index:
                        cell_text = cells[column_index].text.strip()
                        contains_value = search_value in cell_text
                    else:
                        contains_value = search_value in row.text
                else:
                    # Проверяем всю строку
                    contains_value = search_value in row.text

                if not contains_value:
                    mismatched_rows.append(i)
                    if len(mismatched_rows) <= 3:  # Выводим только первые 3 ошибки
                        print(f"  ❌ Строка {i}: НЕ содержит значение '{search_value}'")

            except Exception as e:
                print(f"  ⚠ Ошибка при проверке строки {i}: {e}")
                mismatched_rows.append(i)

        # Выводим результаты
        if mismatched_rows:
            print(f"\n❌ НАЙДЕНЫ НЕСООТВЕТСТВИЯ:")
            print(f"   Всего строк: {len(rows)}")
            print(f"   Строк с несоответствием: {len(mismatched_rows)}")

            if len(mismatched_rows) > 0:
                print(f"   Пример строк с ошибками:")
                for row_num in mismatched_rows[:3]:
                    try:
                        row = rows[row_num - 1]
                        row_text = row.text
                        if len(row_text) > 100:
                            print(f"     Строка {row_num}: {row_text[:100]}...")
                        else:
                            print(f"     Строка {row_num}: {row_text}")
                    except:
                        print(f"     Строка {row_num}: <не удалось получить текст>")

            return False, len(rows), mismatched_rows
        else:
            print(f"\n✅ ВСЕ СТРОКИ СООТВЕТСТВУЮТ!")
            print(f"   Всего строк: {len(rows)}")
            print(f"   Все строки содержат значение: '{search_value}'")
            return True, len(rows), []

    except Exception as e:
        print(f"✗ Ошибка при проверке таблицы: {e}")
        return False, 0, []


def check_column_settings():
    """
    Проверяет настройки столбцов в шестеренке и сверяет с таблицей
    """
    print("\n" + "=" * 50)
    print("ПРОВЕРКА НАСТРОЕК СТОЛБЦОВ (ШЕСТЕРЕНКА)")
    print("=" * 50)

    results = {
        "gear_opened": False,
        "columns_in_gear": {"checked": [], "unchecked": []},
        "columns_in_table": [],
        "match_success": False,
        "details": []
    }

    try:
        # 1. Открываем шестеренку
        print("🔧 Открываем настройки столбцов (шестеренка)...")
        time.sleep(2)

        try:
            # Пробуем найти кнопку шестеренки
            gear_button = driver.find_element(By.CSS_SELECTOR, SETTINGS_GEAR_SELECTOR)
            gear_button.click()
            print("✓ Кликнули на шестеренку")
        except:
            print("⚠ Не удалось найти шестеренку, пробуем через родительский элемент")
            try:
                # Ищем кнопку-родитель
                gear_parent = driver.find_element(By.CSS_SELECTOR,
                                                  "#root > section > section > div > div.mib-profile-control > div.mib-header-right-extra > div > div:nth-child(3) > button")
                gear_parent.click()
                print("✓ Кликнули на кнопку шестеренки через родителя")
            except Exception as e:
                print(f"✗ Не удалось открыть шестеренку: {e}")
                return results

        time.sleep(3)  # Даем больше времени для открытия
        results["gear_opened"] = True

        # 2. Ищем попап
        print("🔍 Ищем попап настроек...")
        time.sleep(2)

        # Пробуем несколько способов найти попап
        popup = None
        try:
            popup = driver.find_element(By.CSS_SELECTOR, SETTINGS_POPUP_SELECTOR)
        except:
            try:
                # Альтернативный селектор
                popup = driver.find_element(By.CSS_SELECTOR, "div.ant-popover.ant-popover-placement-bottomRight")
            except:
                try:
                    # Еще один вариант
                    popup = driver.find_element(By.CSS_SELECTOR, ".ant-popover")
                except:
                    print("⚠ Не удалось найти попап настроек")
                    # Пробуем сделать скриншот для отладки
                    driver.save_screenshot("debug_screenshot.png")
                    print("Скриншот сохранен как debug_screenshot.png")
                    return results

        print("✓ Попап найден")

        # 3. Находим контейнер с настройками столбцов (для скроллинга)
        print("📜 Ищем контейнер с настройками столбцов...")
        content_container = None
        try:
            content_container = driver.find_element(By.CSS_SELECTOR, SETTINGS_CONTENT_ROWS_SELECTOR)
            print("✓ Найден контейнер с настройками")
        except:
            # Пробуем альтернативные селекторы
            try:
                content_container = driver.find_element(By.CSS_SELECTOR, ".user-config-editor-content-rows")
            except:
                try:
                    content_container = popup.find_element(By.CSS_SELECTOR, "div[class*='content-rows']")
                except:
                    print("⚠ Не найден контейнер для скроллинга, ищем строки напрямую")

        # 4. Собираем ВСЕ строки с настройками (со скроллингом)
        print("📋 Собираем информацию о ВСЕХ столбцах...")

        all_row_elements = []

        if content_container:
            # Есть контейнер для скроллинга
            print("📜 Прокручиваем контейнер для сбора всех столбцов...")

            last_height = 0
            max_attempts = 10
            attempt = 0

            while attempt < max_attempts:
                attempt += 1

                # Находим текущие видимые строки
                current_rows = content_container.find_elements(By.CSS_SELECTOR, ".user-config-editor-content-row")

                # Добавляем новые строки
                for row in current_rows:
                    # Проверяем, есть ли уже такая строка
                    row_id = row.id if row.id else row.get_attribute("outerHTML")[:100]
                    if not any(r.id == row_id for r in all_row_elements if hasattr(r, 'id')):
                        all_row_elements.append(row)

                print(f"  📊 Собрано строк: {len(all_row_elements)} (попытка {attempt})")

                # Прокручиваем вниз
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", content_container)
                time.sleep(1)

                # Проверяем, достигли ли мы конца
                new_height = driver.execute_script("return arguments[0].scrollTop", content_container)
                if new_height == last_height:
                    print("  ✓ Достигнут конец списка")
                    break
                last_height = new_height

                # Небольшая задержка
                time.sleep(0.5)
        else:
            # Нет контейнера для скроллинга, собираем все что видно
            print("⚠ Контейнер не найден, собираем видимые строки")
            try:
                all_row_elements = driver.find_elements(By.CSS_SELECTOR, ".user-config-editor-content-row")
            except:
                try:
                    all_row_elements = driver.find_elements(By.XPATH,
                                                            "//div[contains(@class, 'user-config-editor-content-row')]")
                except:
                    pass

        print(f"🔍 Всего найдено строк с настройками: {len(all_row_elements)}")

        # 5. Обрабатываем найденные строки
        for i, row in enumerate(all_row_elements, 1):
            try:
                # Получаем текст строки
                row_text = row.text.strip()
                if not row_text:
                    continue

                # Ищем название столбца (первая строка текста)
                lines = row_text.split('\n')
                column_name = lines[0] if lines else f"Столбец_{i}"

                # Проверяем состояние чекбокса РАЗНЫМИ способами
                is_checked = False

                # Способ 1: Проверяем input checkbox
                try:
                    checkbox_input = row.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                    is_checked = checkbox_input.is_selected()
                    if not is_checked:
                        # Проверяем атрибут checked
                        is_checked = checkbox_input.get_attribute("checked") is not None
                except:
                    pass

                # Способ 2: Проверяем span.ant-checkbox
                if not is_checked:
                    try:
                        checkbox_span = row.find_element(By.CSS_SELECTOR, ".ant-checkbox")
                        is_checked = "ant-checkbox-checked" in checkbox_span.get_attribute("class")
                    except:
                        pass

                # Способ 3: Проверяем по тексту или другим признакам
                if not is_checked:
                    # Проверяем по текстовым признакам
                    is_checked = ("✓" in row_text or
                                  "[x]" in row_text.lower() or
                                  "checked" in row_text.lower() or
                                  "выбран" in row_text.lower())

                # Определяем номер строки для селектора чекбокса
                try:
                    # Пробуем найти родительский контейнер с индексом
                    parent_divs = row.find_elements(By.XPATH,
                                                    "./ancestor::div[contains(@class, 'user-config-editor-content-rows')]/div")
                    if parent_divs:
                        for idx, parent in enumerate(parent_divs, 1):
                            if parent == row or row in parent.find_elements(By.XPATH, ".//*"):
                                row_index = idx
                                # Формируем селектор чекбокса
                                checkbox_selector = CHECKBOX_BASE_SELECTOR.format(row_index)
                                # print(f"  Селектор для строки {i}: {checkbox_selector}")
                                break
                except:
                    pass

                if is_checked:
                    results["columns_in_gear"]["checked"].append(column_name)
                    print(f"  ✓ [{i:3d}] {column_name}")
                else:
                    results["columns_in_gear"]["unchecked"].append(column_name)
                    print(f"  ✗ [{i:3d}] {column_name}")

            except Exception as e:
                print(f"  ⚠ Ошибка в строке {i}: {str(e)[:50]}")

        print(f"\n📊 ИТОГО В ШЕСТЕРЕНКЕ:")
        print(f"  • Отмечено столбцов: {len(results['columns_in_gear']['checked'])}")
        print(f"  • Не отмечено столбцов: {len(results['columns_in_gear']['unchecked'])}")
        print(
            f"  • Всего столбцов: {len(results['columns_in_gear']['checked']) + len(results['columns_in_gear']['unchecked'])}")

        # Выводим примеры отмеченных и неотмеченных столбцов
        if results["columns_in_gear"]["checked"]:
            print(f"  Примеры отмеченных: {', '.join(results['columns_in_gear']['checked'][:5])}")
        if results["columns_in_gear"]["unchecked"]:
            print(f"  Примеры неотмеченных: {', '.join(results['columns_in_gear']['unchecked'][:5])}")

        # 6. Закрываем шестеренку
        print("\n🚫 Закрываем шестеренку...")
        try:
            # Пробуем найти кнопку "Не сохранять" по селектору
            try:
                cancel_button = driver.find_element(By.CSS_SELECTOR, SETTINGS_CANCEL_BUTTON_SELECTOR)
                cancel_button.click()
                print("✓ Нажали 'Не сохранять' (по селектору)")
            except:
                # Пробуем найти кнопку "Не сохранять" по тексту
                cancel_buttons = driver.find_elements(By.XPATH,
                                                      "//button[contains(., 'Не сохранять') or contains(., 'Отмена') or contains(., 'Cancel')]")
                if cancel_buttons:
                    cancel_buttons[0].click()
                    print("✓ Нажали 'Не сохранять' (по тексту)")
                else:
                    # Кликаем вне попапа
                    actions = ActionChains(driver)
                    actions.move_by_offset(10, 10).click().perform()
                    print("✓ Кликнули вне попапа")
        except Exception as e:
            print(f"⚠ Не удалось закрыть шестеренку: {e}")

        time.sleep(2)

        # 7. Проверяем столбцы в таблице
        print("\n🔍 Проверяем столбцы в таблице...")
        wait_for_page_load()
        time.sleep(2)

        try:
            header_cells = driver.find_elements(By.CSS_SELECTOR, f"{TABLE_HEADER_SELECTOR} .BaseTable__header-cell")
            for idx, cell in enumerate(header_cells, 1):
                cell_text = cell.text.strip()
                if cell_text:
                    results["columns_in_table"].append(cell_text)
                    print(f"  [{idx:3d}] {cell_text}")

            print(f"\n📊 Столбцов в таблице: {len(results['columns_in_table'])}")

        except Exception as e:
            print(f"⚠ Ошибка при получении столбцов таблицы: {e}")

        # 8. Точное сравнение столбцов
        print("\n🔍 Точное сравнение столбцов...")

        # Создаем нормализованные версии названий для сравнения
        def normalize_name(name):
            if not name:
                return ""
            # Приводим к нижнему регистру, удаляем лишние пробелы
            name = name.lower().strip()
            # Заменяем ё на е
            name = name.replace('ё', 'е')
            # Удаляем специальные символы
            import re
            name = re.sub(r'[^\wа-я]', '', name)
            return name

        # Нормализуем все названия
        checked_normalized = [normalize_name(name) for name in results["columns_in_gear"]["checked"]]
        unchecked_normalized = [normalize_name(name) for name in results["columns_in_gear"]["unchecked"]]
        table_normalized = [normalize_name(name) for name in results["columns_in_table"]]

        # Проверяем соответствия
        issues_found = []

        # Проверка 1: Все отмеченные в шестеренке должны быть в таблице
        for i, gear_col in enumerate(results["columns_in_gear"]["checked"]):
            gear_norm = checked_normalized[i]
            found = any(table_norm and gear_norm and
                        (gear_norm in table_norm or table_norm in gear_norm)
                        for table_norm in table_normalized)

            if not found:
                issues_found.append(f"Отмеченный столбец '{gear_col}' отсутствует в таблице")

        # Проверка 2: Неотмеченные в шестеренке не должны быть в таблице
        for i, gear_col in enumerate(results["columns_in_gear"]["unchecked"]):
            gear_norm = unchecked_normalized[i]

            for j, table_col in enumerate(results["columns_in_table"]):
                table_norm = table_normalized[j]
                if gear_norm and table_norm and (gear_norm in table_norm or table_norm in gear_norm):
                    issues_found.append(f"Неотмеченный столбец '{gear_col}' присутствует в таблице как '{table_col}'")
                    break

        # Проверка 3: Все столбцы таблицы должны быть либо отмечены, либо не отмечены в шестеренке
        for i, table_col in enumerate(results["columns_in_table"]):
            table_norm = table_normalized[i]
            found_in_gear = False

            # Ищем в отмеченных
            for gear_norm in checked_normalized:
                if table_norm and gear_norm and (table_norm in gear_norm or gear_norm in table_norm):
                    found_in_gear = True
                    break

            # Ищем в неотмеченных
            if not found_in_gear:
                for gear_norm in unchecked_normalized:
                    if table_norm and gear_norm and (table_norm in gear_norm or gear_norm in table_norm):
                        found_in_gear = True
                        break

            if not found_in_gear:
                issues_found.append(f"Столбец таблицы '{table_col}' не найден в настройках шестеренки")

        # Формируем итоговый результат
        if not issues_found:
            results["match_success"] = True
            print("✅ ВСЕ СТОЛБЦЫ СООТВЕТСТВУЮТ НАСТРОЙКАМ!")
            print(f"   • Отмечено в шестеренке: {len(results['columns_in_gear']['checked'])}")
            print(f"   • Отображается в таблице: {len(results['columns_in_table'])}")
            print(f"   • Не отмечено в шестеренке: {len(results['columns_in_gear']['unchecked'])}")
        else:
            results["match_success"] = False
            results["details"] = issues_found

            print("❌ НАЙДЕНЫ НЕСООТВЕТСТВИЯ!")
            print(f"   Всего проблем: {len(issues_found)}")

            for issue in issues_found[:10]:  # Показываем первые 10 проблем
                print(f"   • {issue}")

            if len(issues_found) > 10:
                print(f"   ... и еще {len(issues_found) - 10} проблем")

            print(f"\n   📊 Статистика:")
            print(f"   • Отмечено в шестеренке: {len(results['columns_in_gear']['checked'])}")
            print(f"   • В таблице: {len(results['columns_in_table'])}")
            print(f"   • Не отмечено в шестеренке: {len(results['columns_in_gear']['unchecked'])}")

        print("\n✅ Проверка шестеренки завершена")

    except Exception as e:
        print(f"✗ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

    return results


def click_element(selector, element_name):
    """
    Кликает на элемент по селектору
    """
    try:
        element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        element.click()
        print(f"✓ {element_name}")
        time.sleep(1)
        return True
    except Exception as e:
        print(f"✗ Не удалось кликнуть на {element_name}: {e}")
        return False


# ============================================
# ОСНОВНОЙ СКРИПТ
# ============================================

print("\n" + "=" * 60)
print("КОМПЛЕКСНЫЙ ТЕСТ: ПОИСК + НАСТРОЙКИ СТОЛБЦОВ")
print("=" * 60)

# Хранение результатов
results = {
    "preparation_steps": [],
    "search_tests": [],
    "column_settings_test": None,
    "times": {}
}

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
    print("✓ Авторизация успешна")
    results["preparation_steps"].append("Авторизация - УСПЕШНО")
except Exception as e:
    print(f"✗ Авторизация не удалась: {e}")
    driver.quit()
    exit()

# 2. ПЕРЕХОД В РАЗДЕЛ "РЕЕСТР ВЕДОМОСТЕЙ"
print("\n" + "=" * 50)
print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ 'РЕЕСТР ВЕДОМОСТЕЙ'")
print("=" * 50)

try:
    driver.get('http://10.5.121.74/commercialControl/billingStatements')
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("✓ Переход в раздел 'Реестр ведомостей'")
    results["preparation_steps"].append("Переход в раздел - УСПЕШНО")
    time.sleep(2)
except Exception as e:
    print(f"✗ Не удалось перейти в раздел: {e}")
    driver.quit()
    exit()

# 3. ОТКРЫТИЕ ФИЛЬТРА
print("\n" + "=" * 50)
print("ШАГ 3: ОТКРЫТИЕ ФИЛЬТРА")
print("=" * 50)

if click_element(FILTER_SELECTOR, "Открыли фильтр"):
    results["preparation_steps"].append("Открытие фильтра - УСПЕШНО")

# 4. СБРОС ФИЛЬТРОВ
print("\n" + "=" * 50)
print("ШАГ 4: СБРОС ФИЛЬТРОВ")
print("=" * 50)

if click_element(RESET_SELECTOR, "Сбросили фильтры"):
    results["preparation_steps"].append("Сброс фильтров - УСПЕШНО")

# 5. ОЖИДАНИЕ ЗАГРУЗКИ ПОСЛЕ СБРОСА
print("\n" + "=" * 50)
print("ШАГ 5: ОЖИДАНИЕ ЗАГРУЗКИ ДАННЫХ ПОСЛЕ СБРОСА")
print("=" * 50)

load_duration_reset = wait_for_page_load()
results["times"]["После сброса"] = load_duration_reset

# 6. ПРИМЕНЕНИЕ ФИЛЬТРА
print("\n" + "=" * 50)
print("ШАГ 6: ПРИМЕНЕНИЕ ФИЛЬТРА")
print("=" * 50)

if click_element(APPLY_SELECTOR, "Применили фильтр"):
    results["preparation_steps"].append("Применение фильтра - УСПЕШНО")

# 7. ОЖИДАНИЕ ЗАГРУЗКИ ПОСЛЕ ПРИМЕНЕНИЯ ФИЛЬТРА
print("\n" + "=" * 50)
print("ШАГ 7: ОЖИДАНИЕ ЗАГРУЗКИ ДАННЫХ ПОСЛЕ ПРИМЕНЕНИЯ ФИЛЬТРА")
print("=" * 50)

load_duration_apply = wait_for_page_load()
results["times"]["После применения"] = load_duration_apply

# 8. ВЫПОЛНЕНИЕ ТЕСТОВ ПОИСКА
print("\n" + "=" * 50)
print("ШАГ 8: ВЫПОЛНЕНИЕ ТЕСТОВ ПОИСКА")
print("=" * 50)

for i, test in enumerate(SEARCH_TESTS, 1):
    print(f"\n{'=' * 40}")
    print(f"ТЕСТ {i}: {test['name']}")
    print(f"{'=' * 40}")

    # Выполняем поиск
    search_success = perform_search(test['value'], test['type'])

    # Ждем загрузки
    print("\n⏳ Ожидаем загрузки данных...")
    load_time = wait_for_page_load()

    # Проверяем результаты
    check_success, total_rows, mismatched_rows = check_table_for_value(
        test['value'],
        test.get('column')
    )

    # Сохраняем результаты
    test_result = {
        "name": test['name'],
        "type": test['type'],
        "value": test['value'],
        "search_success": search_success,
        "check_success": check_success,
        "total_rows": total_rows,
        "mismatched_rows": len(mismatched_rows),
        "load_time": load_time
    }

    results["search_tests"].append(test_result)

    # Выводим результат теста
    if check_success and total_rows > 0:
        print(f"\n✅ ТЕСТ '{test['name']}' - ОК")
        print(f"   • Найдено строк: {total_rows}")
        print(f"   • Все строки содержат: '{test['value']}'")
        print(f"   • Время загрузки: {load_time:.1f} сек")
    else:
        print(f"\n❌ ТЕСТ '{test['name']}' - НЕ ОК")
        print(f"   • Найдено строк: {total_rows}")
        print(f"   • Строк с несоответствием: {len(mismatched_rows)}")
        print(f"   • Время загрузки: {load_time:.1f} сек")

    # Очищаем поле поиска (кроме последнего теста)
    if i < len(SEARCH_TESTS):
        if clear_search():
            # Ждем загрузки после очистки
            wait_for_page_load()
            time.sleep(1)

# Очищаем поле поиска в конце
clear_search()
wait_for_page_load()
time.sleep(1)

# 9. ПРОВЕРКА ШЕСТЕРЕНКИ (НАСТРОЙКИ СТОЛБЦОВ)
print("\n" + "=" * 50)
print("ШАГ 9: ПРОВЕРКА НАСТРОЕК СТОЛБЦОВ (ШЕСТЕРЕНКА)")
print("=" * 50)

column_settings_results = check_column_settings()
results["column_settings_test"] = column_settings_results

# 10. ИТОГОВЫЙ ОТЧЕТ
print("\n" + "=" * 60)
print("ИТОГОВЫЙ ОТЧЕТ")
print("=" * 60)

print(f"\n📊 ПОДГОТОВИТЕЛЬНЫЕ ШАГИ:")
for i, step in enumerate(results["preparation_steps"], 1):
    print(f"  {i}. {step}")

print(f"\n⏱️  ВРЕМЯ ВЫПОЛНЕНИЯ ПОДГОТОВКИ:")
for step_name, duration in results["times"].items():
    print(f"  • {step_name}: {duration:.1f} сек")

print(f"\n🔍 РЕЗУЛЬТАТЫ ТЕСТОВ ПОИСКА:")
print("-" * 80)

search_tests_passed = True
for i, test in enumerate(results["search_tests"], 1):
    status = "✅ ОК" if test["check_success"] and test["total_rows"] > 0 else "❌ НЕ ОК"
    print(f"\nТЕСТ {i}: {test['name']}")
    print(f"  Статус: {status}")
    print(f"  Тип поиска: {test['type']}")
    print(f"  Значение: '{test['value']}'")
    print(f"  Найдено строк: {test['total_rows']}")
    print(f"  Время загрузки: {test['load_time']:.1f} сек")

    if not (test["check_success"] and test["total_rows"] > 0):
        search_tests_passed = False

print("-" * 80)

print(f"\n🔧 РЕЗУЛЬТАТ ПРОВЕРКИ ШЕСТЕРЕНКИ:")
print("-" * 80)

if results["column_settings_test"]:
    gear_test = results["column_settings_test"]

    if gear_test["gear_opened"]:
        print(f"✓ Шестеренка открыта успешно")
        print(f"  • Отмечено столбцов в шестеренке: {len(gear_test['columns_in_gear']['checked'])}")
        print(f"  • Не отмечено столбцов: {len(gear_test['columns_in_gear']['unchecked'])}")
        print(f"  • Столбцов в таблице: {len(gear_test['columns_in_table'])}")

        if gear_test["match_success"]:
            print(f"\n✅ ПРОВЕРКА ШЕСТЕРЕНКИ - ОК")
            print("  Все столбцы соответствуют настройкам!")
        else:
            print(f"\n❌ ПРОВЕРКА ШЕСТЕРЕНКИ - НЕ ОК")
            if gear_test["details"]:
                print("  Проблемы:")
                for detail in gear_test["details"]:
                    print(f"    • {detail}")
    else:
        print("✗ Не удалось открыть шестеренку")
else:
    print("✗ Проверка шестеренки не выполнена")

print("-" * 80)

print(f"\n📋 ОБЩИЙ ИТОГ:")
print("-" * 40)

preparation_ok = all(["УСПЕШНО" in step for step in results["preparation_steps"]])
search_ok = search_tests_passed
gear_ok = results["column_settings_test"] and results["column_settings_test"]["match_success"]

print(f"Подготовительные шаги: {'✅' if preparation_ok else '❌'}")
print(f"Тесты поиска: {'✅' if search_ok else '❌'}")
print(f"Проверка шестеренки: {'✅' if gear_ok else '❌'}")

if preparation_ok and search_ok and gear_ok:
    print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
else:
    print("\n⚠ ИМЕЮТСЯ ОШИБКИ В ВЫПОЛНЕНИИ")

print("-" * 40)
print(f"\n{'=' * 60}")

# Пауза для просмотра результата
input("\nНажмите Enter для закрытия браузера...")

# Закрытие браузера
try:
    print("\nЗакрытие браузера...")
    driver.quit()
    print("✓ Браузер успешно закрыт")
except Exception as e:
    print(f"⚠ Не удалось закрыть браузера: {e}")