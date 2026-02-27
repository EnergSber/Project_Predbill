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

# Глобальные переменные
saved_selected_addresses = []
table_selector = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body"  # Добавлено

# Инициализация драйвера
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()
wait = WebDriverWait(driver, 60)

# Данные для авторизации
from config import USERNAME, PASSWORD
URL = 'http://10.5.121.74/login'

# Хранение ошибок
section_errors = []

print("=" * 60)
print("ТЕСТ РАЗДЕЛА: Реестр ведомостей - Отклонение")
print("=" * 60)


# ФУНКЦИЯ ДЛЯ ДОБАВЛЕНИЯ ОШИБОК
def add_error(error_text):
    if error_text not in section_errors:
        section_errors.append(error_text)
        print(f"ОШИБКА: {error_text}")


# ФУНКЦИЯ ДЛЯ ПРОВЕРКИ АДРЕСОВ В МОДАЛЬНОМ ОКНЕ
def verify_addresses_in_modal():
    try:
        print("\nПроверяем адреса в модальном окне...")

        # Даем время на загрузку модального окна
        time.sleep(2)

        # Сначала получим HTML модального окна для отладки
        try:
            modal = driver.find_element(By.CSS_SELECTOR, ".ant-modal")
            modal_html = modal.get_attribute('outerHTML')
            print(f"  HTML модального окна (первые 500 символов): {modal_html[:500]}...")
        except:
            print("  Не удалось получить HTML модального окна")

        # Пробуем найти любой текст в модальном окне
        try:
            modal_body = driver.find_element(By.CSS_SELECTOR, ".ant-modal-body")
            modal_text = modal_body.text
            print(f"  Текст модального окна:\n{modal_text}")

            # Разделим текст на строки
            lines = [line.strip() for line in modal_text.split('\n') if line.strip()]
            print(f"  Найдено {len(lines)} строк в модальном окне:")
            for i, line in enumerate(lines, 1):
                print(f"    {i}. {line}")

            # Ищем адреса в тексте
            addresses_in_modal = []
            for line in lines:
                if any(keyword in line.lower() for keyword in ['ул.', 'д.', 'просп.', 'бульв.', 'шоссе', 'пер.']):
                    addresses_in_modal.append(line)

            # Получаем сохраненные адреса
            global saved_selected_addresses

            print(f"\nСохраненные адреса (из таблицы):")
            for i, addr in enumerate(saved_selected_addresses, 1):
                print(f"  {i}. {addr}")

            print(f"\nНайденные адреса в модальном окне:")
            for i, addr in enumerate(addresses_in_modal, 1):
                print(f"  {i}. {addr}")

            # Сравниваем адреса
            if not saved_selected_addresses:
                print("  ВНИМАНИЕ: Нет сохраненных адресов для сравнения")
                return False

            if not addresses_in_modal:
                print("  ВНИМАНИЕ: Не найдены адреса в модальном окне")
                return False

            # Упрощенное сравнение: ищем частичные совпадения
            matches_found = 0
            for saved_addr in saved_selected_addresses:
                found = False
                # Берем ключевую часть адреса (первые слова)
                saved_key_parts = saved_addr.split(',')[0]  # Например, "бульв. Маршала Рокоссовского"

                for modal_addr in addresses_in_modal:
                    if saved_key_parts in modal_addr:
                        matches_found += 1
                        print(f"  ✓ Совпадение: '{saved_key_parts}' найдено в '{modal_addr}'")
                        found = True
                        break

                if not found:
                    print(f"  ✗ Адрес не найден в модальном окне: {saved_addr}")

            if matches_found == len(saved_selected_addresses):
                print(f"\n  УСПЕХ: Все {matches_found} адреса совпадают!")
                return True
            else:
                print(f"\n  ПРОБЛЕМА: Найдено только {matches_found} из {len(saved_selected_addresses)} совпадений")
                return matches_found > 0

        except Exception as e:
            print(f"  Ошибка при анализе модального окна: {e}")
            return False

    except Exception as e:
        print(f"  Ошибка при проверке адресов в модальном окне: {e}")
        return False


# ФУНКЦИЯ ДЛЯ ПРОВЕРКИ ВЫБРАННЫХ ВЕДОМОСТЕЙ
def verify_selected_statements():
    try:
        print("\nПроверяем выбранные ведомости...")

        # Сначала запоминаем адреса отмеченных ведомостей
        selected_addresses = []

        # Ищем таблицу
        table_body = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, table_selector))
        )

        # Ищем все строки в таблице
        rows = table_body.find_elements(By.CSS_SELECTOR, "div.BaseTable__row")

        if len(rows) == 0:
            print("Таблица пуста")
            return False

        print(f"Найдено строк в таблице: {len(rows)}")

        # Проверяем первые 5 строк
        check_rows = min(5, len(rows))
        print(f"Проверяем первые {check_rows} строк...")

        for i in range(check_rows):
            try:
                row = rows[i]

                # Ищем чекбокс
                checkbox = row.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                is_selected = checkbox.is_selected()

                # Получаем адрес из 5-й ячейки (индекс 4)
                cells = row.find_elements(By.CSS_SELECTOR, ".BaseTable__row-cell")

                if len(cells) >= 5:
                    # Получаем ячейку с адресом (4-я по счету, индекс 4)
                    address_cell = cells[4]

                    # Внутри ячейки ищем элемент с классом textEllipsis
                    try:
                        # Первый способ: ищем span с классом textEllipsis
                        address_element = address_cell.find_element(By.CSS_SELECTOR, "span.textEllipsis")
                        address = address_element.text.strip()
                    except:
                        # Второй способ: если элемент не найден, берем весь текст ячейки
                        address = address_cell.text.strip()

                        # Очищаем адрес от лишних символов
                        address = address.replace('\n', ' ')

                        # Убираем иконку (она может быть в тексте)
                        if 'svg' in address_cell.get_attribute('outerHTML'):
                            # Пытаемся найти только текст после иконки
                            import re
                            text_match = re.search(r'<span[^>]*>([^<]+)</span>',
                                                   address_cell.get_attribute('outerHTML'))
                            if text_match:
                                address = text_match.group(1).strip()
                else:
                    address = "Адрес не найден"

                status = "✓" if is_selected else "✗"
                print(f"  Строка {i + 1}: {status} {address}")

                if is_selected:
                    selected_addresses.append(address)

            except Exception as e:
                print(f"  Ошибка при проверке строки {i + 1}: {str(e)[:50]}")
                continue

        print(f"\nВсего отмечено ведомостей: {len(selected_addresses)}")

        if len(selected_addresses) == 0:
            add_error("Не отмечено ни одной ведомости")
            return False

        if len(selected_addresses) < 3:
            print(f"ВНИМАНИЕ: Отмечено только {len(selected_addresses)} ведомостей, ожидалось 3")
            return False

        # Сохраняем адреса для проверки после сохранения
        global saved_selected_addresses
        saved_selected_addresses = selected_addresses

        print("Отмеченные адреса сохранены для проверки")
        print("Сохраненные адреса:")
        for i, addr in enumerate(selected_addresses, 1):
            print(f"  {i}. {addr}")

        return True

    except Exception as e:
        print(f"Ошибка при проверке ведомостей: {e}")
        return False


# ФУНКЦИЯ ДЛЯ ПРОВЕРКИ УСПЕШНОСТИ ОПЕРАЦИИ ПОСЛЕ СОХРАНЕНИЯ
def check_operation_success():
    try:
        print("\nПроверяем успешность операции отклонения...")
        time.sleep(3)

        success = False

        # 1. Проверяем сообщение об успехе
        success_selectors = [
            "div.ant-notification-notice-success",
            "div.ant-alert-success",
            ".ant-message-success",
            "[class*='success']"
        ]

        for selector in success_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    try:
                        if elem.is_displayed():
                            success_text = elem.text.strip()
                            if success_text and len(success_text) > 3:
                                print(f"Успешное сообщение: {success_text}")
                                success = True
                                break
                    except:
                        continue
                if success:
                    break
            except:
                continue

        # 2. Проверяем что модальное окно закрылось
        if not success:
            try:
                # Ищем модальное окно
                modal = driver.find_element(By.CSS_SELECTOR, ".ant-modal")
                if not modal.is_displayed():
                    print("Модальное окно закрылось - операция выполнена")
                    success = True
            except:
                print("Модальное окно не найдено - вероятно закрылось")
                success = True

        # 3. Проверяем что отмеченные ведомости больше не отмечены
        if success and saved_selected_addresses:  # Исправлено: проверяем глобальную переменную
            try:
                print("Проверяем обновление таблицы...")
                time.sleep(2)

                # Используем глобальную переменную table_selector
                global table_selector
                table_body = driver.find_element(By.CSS_SELECTOR, table_selector)
                rows = table_body.find_elements(By.CSS_SELECTOR, "div.BaseTable__row")

                # Проверяем что первые три чекбокса сняты
                first_three_checked = 0
                for i in range(min(3, len(rows))):
                    try:
                        checkbox = rows[i].find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                        if checkbox.is_selected():
                            first_three_checked += 1
                    except:
                        continue

                if first_three_checked == 0:
                    print("Первые три ведомости больше не отмечены - операция выполнена")
                else:
                    print(f"Предупреждение: {first_three_checked} из первых трех ведомостей все еще отмечены")

            except Exception as e:
                print(f"Не удалось проверить обновление таблицы: {e}")

        return success

    except Exception as e:
        print(f"Ошибка при проверке успешности операции: {e}")
        return True


# ФУНКЦИЯ ДЛЯ ПРОВЕРКИ ЧТО НУЖНЫЕ ВЕДОМОСТИ ОТМЕЧЕНЫ
def verify_first_three_selected():
    try:
        print("\nПроверяем что отмечены первые три ведомости...")

        # Используем глобальную переменную table_selector
        global table_selector
        table_body = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, table_selector))
        )

        # Ищем все строки в таблице
        rows = table_body.find_elements(By.CSS_SELECTOR, "div.BaseTable__row")

        if len(rows) < 3:
            add_error(f"В таблице меньше 3 строк: {len(rows)}")
            return False

        # Проверяем первые три строки
        first_three_selected = True
        for i in range(3):
            try:
                checkbox = rows[i].find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                if not checkbox.is_selected():
                    print(f"  Строка {i + 1}: НЕ отмечена!")
                    first_three_selected = False
                    # Отмечаем если не отмечена
                    checkbox.click()
                    time.sleep(0.2)
                    print(f"  Строка {i + 1}: теперь отмечена")
                else:
                    print(f"  Строка {i + 1}: отмечена ✓")
            except Exception as e:
                print(f"  Ошибка при проверке строки {i + 1}: {e}")
                first_three_selected = False

        return first_three_selected

    except Exception as e:
        add_error(f"Ошибка при проверке первых трех ведомостей: {e}")
        return False


# ФУНКЦИЯ ДЛЯ ПРОВЕРКИ И ЗАКРЫТИЯ ОШИБОК
def check_and_close_errors(step_name=""):
    try:
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
                                error_msg = f"{step_name}: {error_text}" if step_name else error_text
                                add_error(error_msg)
                                error_found = True

                                # Пытаемся закрыть ошибку
                                close_selectors = [
                                    "span.ant-notification-notice-close-x",
                                    ".ant-notification-notice-close",
                                    ".ant-alert-close-icon",
                                    "[aria-label='close']",
                                    ".anticon-close"
                                ]

                                for close_selector in close_selectors:
                                    try:
                                        close_btn = elem.find_element(By.CSS_SELECTOR, close_selector)
                                        if close_btn.is_displayed():
                                            close_btn.click()
                                            time.sleep(0.2)
                                            break
                                    except:
                                        continue
                    except:
                        continue
            except:
                continue

        return error_found

    except Exception as e:
        print(f"Ошибка при проверке ошибок: {e}")
        return False


# ФУНКЦИЯ ДЛЯ ОЖИДАНИЯ ЗАГРУЗКИ
def wait_for_page_load():
    print("Ожидание загрузки данных...")
    time.sleep(1)

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

        print("Загрузка данных завершена")
        return True

    except Exception as e:
        print(f"Ошибка при ожидании загрузки: {e}")
        return False


# ФУНКЦИЯ ДЛЯ НАЖАТИЯ TAB
def press_tab():
    try:
        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB).perform()
        time.sleep(0.3)
        return True
    except Exception as e:
        print(f"Ошибка при нажатии Tab: {e}")
        return False


# ФУНКЦИЯ ДЛЯ ВЫБОРА КАТЕГОРИЙ
def select_categories():
    try:
        print("Устанавливаем категории...")

        # Селектор для поля "Категория"
        category_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(2) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div > div.ant-select-selection-overflow"

        # Находим поле
        field_element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, category_selector))
        )

        # Прокручиваем и кликаем
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field_element)
        time.sleep(0.5)
        field_element.click()
        time.sleep(1)

        # Ищем выпадающий список
        dropdown = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ant-select-dropdown:not(.ant-select-dropdown-hidden)"))
        )

        # Ищем нужные опции
        categories_to_select = []

        # Ищем все опции
        all_options = dropdown.find_elements(By.CSS_SELECTOR, ".ant-select-item-option")
        print(f"Найдено опций категорий: {len(all_options)}")

        # Ищем нужные категории
        target_categories = ["Tн.р. = 0", "Тн.р. = 0", "Tн.р. < 15 суток", "Тн.р. < 15 суток"]

        for option in all_options:
            try:
                text = option.text.strip()
                for target in target_categories:
                    if text == target:
                        categories_to_select.append((option, text))
                        print(f"Найдена нужная категория: '{text}'")
                        break
            except:
                continue

        # Выбираем найденные категории
        selected_count = 0
        for option, text in categories_to_select:
            try:
                option.click()
                print(f"Выбрана категория: '{text}'")
                selected_count += 1
                time.sleep(0.5)
            except:
                continue

        # Закрываем список
        field_element.click()

        if selected_count >= 2:  # Нужно выбрать хотя бы 2 категории
            print(f"Выбрано категорий: {selected_count}")

            # Проверяем что не выбраны лишние категории
            selected_text = field_element.text.strip()
            if "Tн.р. > 15" in selected_text or "> 15 суток" in selected_text:
                add_error("Выбраны лишние категории с '> 15 суток'")
                return False

            return True
        else:
            add_error(f"Выбрано недостаточно категорий: {selected_count}")
            return False

    except Exception as e:
        add_error(f"Ошибка при выборе категорий: {e}")
        return False


# ФУНКЦИЯ ДЛЯ ВЫБОРА СТАТУСОВ
def select_statuses():
    try:
        print("Устанавливаем статусы ведомости...")

        # Селектор для поля "Статус ведомости"
        status_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(3) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div"

        # Находим поле
        field_element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, status_selector))
        )

        # Прокручиваем и кликаем
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field_element)
        time.sleep(0.5)
        field_element.click()
        time.sleep(1)

        # Ищем выпадающий список
        dropdown = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ant-select-dropdown:not(.ant-select-dropdown-hidden)"))
        )

        # Ищем нужные статусы
        statuses_to_select = []
        target_statuses = ["Отправлена", "Не отправлена"]

        # Ищем все опции
        all_options = dropdown.find_elements(By.CSS_SELECTOR, ".ant-select-item-option")

        for option in all_options:
            try:
                text = option.text.strip()
                for target in target_statuses:
                    if text == target:
                        statuses_to_select.append((option, text))
                        print(f"Найден статус: '{text}'")
                        break
            except:
                continue

        # Выбираем найденные статусы
        selected_count = 0
        for option, text in statuses_to_select:
            try:
                option.click()
                print(f"Выбран статус: '{text}'")
                selected_count += 1
                time.sleep(0.5)
            except:
                continue

        # Закрываем список
        field_element.click()

        if selected_count >= 2:
            print(f"Выбрано статусов: {selected_count}")
            return True
        else:
            add_error(f"Выбрано недостаточно статусов: {selected_count}")
            return False

    except Exception as e:
        add_error(f"Ошибка при выборе статусов: {e}")
        return False


# ФУНКЦИЯ ДЛЯ ПРИМЕНЕНИЯ ФИЛЬТРОВ
def apply_filters():
    try:
        print("Применяем фильтры...")

        # Селектор для кнопки "Применить"
        apply_button_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > div > div.filterOperations > button:nth-child(1) > span > svg"

        # Находим и кликаем
        apply_svg = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, apply_button_selector))
        )

        # Кликаем через родительский элемент
        parent_button = apply_svg.find_element(By.XPATH, "..")
        parent_button.click()
        print("Фильтры применены")

        # Ожидаем загрузки
        wait_for_page_load()

        # Проверяем ошибки
        check_and_close_errors("После применения фильтров")

        return True

    except Exception as e:
        add_error(f"Ошибка при применении фильтров: {e}")
        return False


# ФУНКЦИЯ ДЛЯ ОТМЕТКИ ЧЕКБОКСОВ
def mark_checkboxes():
    try:
        print("Отмечаем первые три чекбокса...")

        # Используем глобальную переменную table_selector
        global table_selector
        table_body = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, table_selector))
        )

        # Ищем строки
        rows = table_body.find_elements(By.CSS_SELECTOR, "div.BaseTable__row")

        if len(rows) < 3:
            add_error(f"В таблице меньше 3 строк: {len(rows)}")
            return False

        # Отмечаем первые три чекбокса
        marked_count = 0
        for i in range(3):
            try:
                # Ищем чекбокс в строке
                checkbox = rows[i].find_element(By.CSS_SELECTOR, "input[type='checkbox']")

                # Прокручиваем
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                time.sleep(0.3)

                # Кликаем если не отмечен
                if not checkbox.is_selected():
                    checkbox.click()
                    marked_count += 1
                    print(f"Отмечен чекбокс {i + 1}")
                    time.sleep(0.3)
                else:
                    print(f"Чекбокс {i + 1} уже отмечен")
                    marked_count += 1

            except Exception as e:
                print(f"Ошибка при отметке чекбокса {i + 1}: {e}")

        if marked_count == 3:
            print("Все три чекбокса отмечены")
            return True
        else:
            add_error(f"Отмечено только {marked_count} из 3 чекбоксов")
            return marked_count > 0

    except Exception as e:
        add_error(f"Ошибка при отметке чекбоксов: {e}")
        return False


# ФУНКЦИЯ ДЛЯ КЛИКА НА КНОПКУ "ДЕЙСТВИЕ"
def click_action_button():
    try:
        print("Кликаем на кнопку 'Действие'...")

        # Ищем кнопку по классу
        action_button = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.ant-btn.ant-btn-link.ant-dropdown-trigger.inlineButton"))
        )

        # Прокручиваем и кликаем
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", action_button)
        time.sleep(0.5)
        action_button.click()
        print("Кнопка 'Действие' нажата")
        time.sleep(1)

        return True

    except Exception as e:
        add_error(f"Ошибка при клике на кнопку 'Действие': {e}")
        return False


# ФУНКЦИЯ ДЛЯ ВЫБОРА ОПЦИИ "ОТКЛОНИТЬ"
def select_reject_option():
    try:
        print("Выбираем опцию 'Отклонить'...")

        # Ищем элемент с текстом "Отклонить"
        reject_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Отклонить')]")

        for element in reject_elements:
            try:
                if element.is_displayed() and element.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.5)
                    element.click()
                    print("Опция 'Отклонить' выбрана")
                    time.sleep(1)

                    # Проверяем ошибки
                    check_and_close_errors("После выбора 'Отклонить'")

                    return True
            except:
                continue

        add_error("Не найден элемент 'Отклонить'")
        return False

    except Exception as e:
        add_error(f"Ошибка при выборе опции 'Отклонить': {e}")
        return False


# ФУНКЦИЯ ДЛЯ ВЫБОРА ПРИЧИНЫ ОТКЛОНЕНИЯ
def select_reject_reason():
    try:
        print("Выбираем причину отклонения...")

        # Ждем появления модального окна
        time.sleep(2)

        # Ищем контейнер поля причины по указанному селектору
        reason_container_selector = "#addRolesModalForm > div.rt-form-body > div.flexBetween > div > div > div.ant-col.ant-col-28.ant-form-item-control > div > div > div > div"

        reason_container = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, reason_container_selector))
        )

        # Прокручиваем к контейнеру
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reason_container)
        time.sleep(0.5)

        print("Нашли контейнер поле причины")

        # СНАЧАЛА проверяем, может поле уже открыто
        try:
            # Ищем открытый выпадающий список
            open_dropdown = driver.find_element(By.CSS_SELECTOR,
                                                ".ant-select-dropdown:not(.ant-select-dropdown-hidden)")
            print("Выпадающий список уже открыт")
        except:
            # Если не открыт, кликаем чтобы открыть
            print("Кликаем чтобы открыть список причин...")
            reason_container.click()
            time.sleep(1)

        # Ждем появления выпадающего списка
        try:
            # Даем больше времени для загрузки
            time.sleep(1.5)

            # Ищем выпадающий список причин
            reason_list = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".ant-select-dropdown:not(.ant-select-dropdown-hidden)"))
            )
            print("Выпадающий список причин найден")

        except Exception as e:
            print(f"Не видим выпадающий список: {e}")

            # Пробуем кликнуть еще раз
            print("Пробуем кликнуть еще раз...")
            reason_container.click()
            time.sleep(1.5)

            reason_list = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".ant-select-dropdown:not(.ant-select-dropdown-hidden)"))
            )
            print("Выпадающий список появился после повторного клика")

        # Ищем все опции в списке
        reason_options = reason_list.find_elements(By.CSS_SELECTOR, ".ant-select-item-option")

        if not reason_options:
            # Пробуем другие селекторы
            reason_options = reason_list.find_elements(By.CSS_SELECTOR, "div[role='option']")
            reason_options = reason_list.find_elements(By.CSS_SELECTOR, "div.ant-select-item")

        if not reason_options:
            add_error("Список причин пуст")
            return False

        print(f"Найдено причин для выбора: {len(reason_options)}")

        # Выводим доступные причины для отладки
        print("Доступные причины:")
        for i, option in enumerate(reason_options[:10]):  # Показываем первые 10
            try:
                text = option.text.strip()
                if text:
                    print(f"  {i + 1}. '{text}'")
            except:
                continue

        # Выбираем случайную причину (из тех что не пустые)
        valid_options = []
        for option in reason_options:
            try:
                text = option.text.strip()
                if text and text != "" and text != "Выберите значение":
                    valid_options.append(option)
            except:
                continue

        if not valid_options:
            add_error("Нет доступных причин для выбора")
            return False

        # Выбираем случайную причину
        random_option = random.choice(valid_options)

        # Получаем текст перед кликом
        reason_text = random_option.text.strip()

        # Прокручиваем к выбранному элементу
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", random_option)
        time.sleep(0.3)

        # Кликаем на случайную причину
        random_option.click()
        print(f"Выбрана причина: '{reason_text}'")
        time.sleep(0.5)

        # Ждем пока список закроется
        time.sleep(1)

        # ПРОВЕРЯЕМ что значение выбралось в поле
        try:
            # Ищем поле с выбранным значением
            selected_value = driver.find_element(By.CSS_SELECTOR,
                                                 f"{reason_container_selector} .ant-select-selection-item")
            selected_text = selected_value.text.strip()
            print(f"В поле выбрано: '{selected_text}'")

            if not selected_text or selected_text == "Выберите значение":
                print("Предупреждение: значение в поле не изменилось")
                # Пробуем выбрать еще раз первую доступную причину
                if valid_options:
                    first_option = valid_options[0]
                    first_option.click()
                    print("Повторно выбрана первая причина")
                    time.sleep(0.5)
        except:
            print("Не удалось проверить выбранное значение в поле")

        # Проверяем ошибки
        check_and_close_errors("После выбора причины")

        return True

    except Exception as e:
        add_error(f"Ошибка при выборе причины: {e}")
        print(f"Детали ошибки: {str(e)}")

        # Пробуем альтернативный способ через JavaScript
        try:
            print("Пробуем альтернативный способ через JavaScript...")

            # Находим все опции в выпадающем списке
            dropdown = driver.find_element(By.CSS_SELECTOR, ".ant-select-dropdown")
            options = dropdown.find_elements(By.CSS_SELECTOR, ".ant-select-item-option")

            if options:
                # Выбираем первую опцию
                js_script = """
                var options = arguments[0].querySelectorAll('.ant-select-item-option');
                if (options.length > 0) {
                    options[0].click();
                    return true;
                }
                return false;
                """

                result = driver.execute_script(js_script, dropdown)
                if result:
                    print("Причина выбрана через JavaScript")
                    time.sleep(1)
                    return True

        except Exception as js_error:
            print(f"JavaScript способ тоже не сработал: {js_error}")

        return False


# ФУНКЦИЯ ДЛЯ НАЖАТИЯ КНОПКИ "СОХРАНИТЬ"
def click_save_button():
    try:
        print("Нажимаем кнопку 'Сохранить'...")

        # Даем время для загрузки модального окна
        time.sleep(2)

        # СПОСОБ 1: Ищем по ID формы и кнопке
        try:
            save_button = driver.find_element(By.CSS_SELECTOR,
                                              "#addRolesModalForm > div.rt-form-footer > button.ant-btn.ant-btn-primary.ml-s")
            if save_button.is_displayed() and save_button.is_enabled():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_button)
                time.sleep(0.5)
                save_button.click()
                print("Кнопка 'Сохранить' нажата")
                time.sleep(2)

                # Проверяем ошибки после сохранения
                check_and_close_errors("После нажатия 'Сохранить'")

                return True
        except:
            pass

        # СПОСОБ 2: Ищем по тексту "Сохранить"
        save_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Сохранить')]")

        for button in save_buttons:
            try:
                if button.is_displayed() and button.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    time.sleep(0.5)
                    button.click()
                    print("Кнопка 'Сохранить' нажата (по тексту)")
                    time.sleep(2)

                    # Проверяем ошибки после сохранения
                    check_and_close_errors("После нажатия 'Сохранить'")

                    return True
            except:
                continue

        # СПОСОБ 3: Ищем по классу основной кнопки
        try:
            primary_buttons = driver.find_elements(By.CSS_SELECTOR, "button.ant-btn-primary")
            for button in primary_buttons:
                try:
                    button_text = button.text.strip()
                    if button.is_displayed() and button.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        time.sleep(0.5)
                        button.click()
                        print(f"Кнопка '{button_text}' нажата (по классу primary)")
                        time.sleep(2)
                        check_and_close_errors("После нажатия кнопки")
                        return True
                except:
                    continue
        except:
            pass

        # СПОСОБ 4: Ищем в модальном окне
        try:
            modal_buttons = driver.find_elements(By.CSS_SELECTOR, ".ant-modal-footer button")
            for button in modal_buttons:
                try:
                    button_text = button.text.strip()
                    if button_text == "Сохранить" or button_text == "OK" or button_text == "Да":
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            print(f"Кнопка '{button_text}' нажата (в модальном окне)")
                            time.sleep(2)
                            return True
                except:
                    continue
        except:
            pass

        add_error("Не найдена кнопка 'Сохранить'")
        return False

    except Exception as e:
        add_error(f"Ошибка при нажатии кнопки 'Сохранить': {e}")
        return False


# ФУНКЦИЯ ДЛЯ КЛИКА НА SVG ЭЛЕМЕНТ
def click_svg_element(svg_selector, action_name):
    try:
        svg_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, svg_selector))
        )

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", svg_element)
        time.sleep(0.3)

        # Пытаемся кликнуть через родительский элемент
        try:
            parent_button = svg_element.find_element(By.XPATH, "..")
            parent_button.click()
        except:
            svg_element.click()

        print(f"{action_name}")
        time.sleep(0.5)
        return True

    except Exception as e:
        add_error(f"Не удалось {action_name}: {e}")
        return False


# ОСНОВНОЙ КОД
try:
    # 1. АВТОРИЗАЦИЯ
    print("\n" + "=" * 50)
    print("ШАГ 1: АВТОРИЗАЦИЯ")
    print("=" * 50)

    driver.get(URL)
    username_field = wait.until(EC.presence_of_element_located((By.ID, "normal_login_username")))
    username_field.send_keys(USERNAME)
    password_field = driver.find_element(By.ID, "normal_login_password")
    password_field.send_keys(PASSWORD)
    login_button = driver.find_element(By.CSS_SELECTOR, '.ant-btn.ant-btn-primary.w-100.mb-s')
    login_button.click()
    wait.until_not(EC.url_contains('login'))
    print("Авторизация успешна")

    # Проверяем ошибки
    check_and_close_errors("После авторизации")

    # 2. ПЕРЕХОД В РАЗДЕЛ
    print("\n" + "=" * 50)
    print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ")
    print("=" * 50)

    section_url = 'http://10.5.121.74/commercialControl/billingStatements'
    driver.get(section_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("Переход в раздел 'Реестр ведомостей'")
    time.sleep(2)

    # Проверяем ошибки
    check_and_close_errors("После перехода в раздел")

    # 3. ОТКРЫТИЕ ФИЛЬТРА
    print("\n" + "=" * 50)
    print("ШАГ 3: ОТКРЫТИЕ ФИЛЬТРА")
    print("=" * 50)

    if not click_svg_element("svg[data-icon='filter']", "Фильтр открыт"):
        raise Exception("Не удалось открыть фильтр")

    time.sleep(2)

    # Проверяем ошибки
    check_and_close_errors("После открытия фильтра")

    # 4. СБРОС ФИЛЬТРОВ
    print("\n" + "=" * 50)
    print("ШАГ 4: СБРОС ФИЛЬТРОВ")
    print("=" * 50)

    if not click_svg_element("svg[data-icon='stop']", "Фильтры сброшены"):
        print("Предупреждение: не удалось сбросить фильтры")

    time.sleep(1)
    wait_for_page_load()

    # Проверяем ошибки
    check_and_close_errors("После сброса фильтров")

    # 5. УСТАНОВКА КАТЕГОРИЙ
    print("\n" + "=" * 50)
    print("ШАГ 5: УСТАНОВКА КАТЕГОРИЙ")
    print("=" * 50)

    if not select_categories():
        add_error("Не удалось установить категории")

    # Нажимаем Tab
    press_tab()

    # Проверяем ошибки
    check_and_close_errors("После установки категорий")

    # 6. УСТАНОВКА СТАТУСОВ
    print("\n" + "=" * 50)
    print("ШАГ 6: УСТАНОВКА СТАТУСОВ")
    print("=" * 50)

    if not select_statuses():
        add_error("Не удалось установить статусы")

    # Нажимаем Tab
    press_tab()

    # Проверяем ошибки
    check_and_close_errors("После установки статусов")

    # 7. ПРИМЕНЕНИЕ ФИЛЬТРОВ
    print("\n" + "=" * 50)
    print("ШАГ 7: ПРИМЕНЕНИЕ ФИЛЬТРОВ")
    print("=" * 50)

    if not apply_filters():
        add_error("Не удалось применить фильтры")

    # 8. ОТМЕТКА ЧЕКБОКСОВ
    print("\n" + "=" * 50)
    print("ШАГ 8: ОТМЕТКА ЧЕКБОКСОВ")
    print("=" * 50)

    if not mark_checkboxes():
        add_error("Не удалось отметить чекбоксы")

    # Проверяем ошибки
    check_and_close_errors("После отметки чекбоксов")

    # 9. КЛИК НА "ДЕЙСТВИЕ"
    print("\n" + "=" * 50)
    print("ШАГ 9: КЛИК НА КНОПКУ 'ДЕЙСТВИЕ'")
    print("=" * 50)

    if not click_action_button():
        add_error("Не удалось нажать кнопку 'Действие'")

    # 10. ВЫБОР "ОТКЛОНИТЬ"
    print("\n" + "=" * 50)
    print("ШАГ 10: ВЫБОР ОПЦИИ 'ОТКЛОНИТЬ'")
    print("=" * 50)

    if not select_reject_option():
        add_error("Не удалось выбрать опцию 'Отклонить'")

        # 11. ВЫБОР ПРИЧИНЫ ОТКЛОНЕНИЯ
    print("\n" + "=" * 50)
    print("ШАГ 11: ВЫБОР ПРИЧИНЫ ОТКЛОНЕНИЯ")
    print("=" * 50)

    if not select_reject_reason():
        add_error("Не удалось выбрать причину отклонения")

    # 12. ПРОВЕРКА ВЫБРАННЫХ ВЕДОМОСТЕЙ (ПЕРЕД проверкой модального окна)
    print("\n" + "=" * 50)
    print("ШАГ 12: ПРОВЕРКА ВЫБРАННЫХ ВЕДОМОСТЕЙ")
    print("=" * 50)

    # Проверяем что отмечены первые три ведомости
    if not verify_first_three_selected():
        add_error("Не все первые три ведомости отмечены")

    # Проверяем что отмеченные ведомости соответствуют фильтрам (упрощенная проверка)
    verify_selected_statements()

    # 13. ПРОВЕРКА АДРЕСОВ В МОДАЛЬНОМ ОКНЕ
    print("\n" + "=" * 50)
    print("ШАГ 13: ПРОВЕРКА АДРЕСОВ В МОДАЛЬНОМ ОКНЕ")
    print("=" * 50)

    if not verify_addresses_in_modal():
        print("Предупреждение: адреса в модальном окне не полностью совпадают с выбранными")

    # 14. НАЖАТИЕ "СОХРАНИТЬ"
    print("\n" + "=" * 50)
    print("ШАГ 14: НАЖАТИЕ КНОПКИ 'СОХРАНИТЬ'")
    print("=" * 50)

    if not click_save_button():
        add_error("Не удалось нажать кнопку 'Сохранить'")

    # 15. ФИНАЛЬНАЯ ПРОВЕРКА
    print("\n" + "=" * 50)
    print("ШАГ 15: ФИНАЛЬНАЯ ПРОВЕРКА")
    print("=" * 50)

    # Проверяем ошибки финально
    check_and_close_errors("Финальная проверка")

    # Проверяем успешность операции
    try:
        # Ищем сообщение об успехе
        success_selectors = [
            "div.ant-notification-notice-success",
            "div.ant-alert-success",
            ".ant-message-success",
            "[class*='success']"
        ]

        success_found = False
        for selector in success_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    try:
                        if elem.is_displayed():
                            success_text = elem.text.strip()
                            if success_text and len(success_text) > 3:
                                print(f"Успешное сообщение: {success_text}")
                                success_found = True
                                break
                    except:
                        continue
                if success_found:
                    break
            except:
                continue

        if not success_found:
            print("Сообщение об успехе не найдено, проверяем обновление таблицы...")

            # Проверяем что отмеченные ведомости исчезли или изменили статус
            try:
                # Используем глобальную переменную table_selector

                table_body = driver.find_element(By.CSS_SELECTOR, table_selector)
                rows = table_body.find_elements(By.CSS_SELECTOR, "div.BaseTable__row")

                # Проверяем что первые три чекбокса сняты
                first_three_checked = 0
                for i in range(min(3, len(rows))):
                    try:
                        checkbox = rows[i].find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                        if checkbox.is_selected():
                            first_three_checked += 1
                    except:
                        continue

                if first_three_checked == 0:
                    print("Первые три ведомости больше не отмечены - операция выполнена")
                else:
                    print(f"Предупреждение: {first_three_checked} из первых трех ведомостей все еще отмечены")

            except Exception as e:
                print(f"Не удалось проверить обновление таблицы: {e}")

    except Exception as e:
        print(f"Ошибка при проверке успешности операции: {e}")

    # Проверяем ошибки финально
    check_and_close_errors("Финальная проверка")

    # 15. ИТОГОВЫЙ ОТЧЕТ
    print("\n" + "=" * 60)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)

    print("Все шаги выполнены")

    if section_errors:
        print(f"\nНайдено ошибок: {len(section_errors)}")
        for i, error in enumerate(section_errors, 1):
            print(f"{i}. {error}")
    else:
        print("\nОшибок не обнаружено")

    print("\nТест завершен")

except Exception as e:
    add_error(f"Критическая ошибка в основном потоке: {e}")
    print(f"\nТест прерван с ошибкой: {e}")

finally:
    #input()
    try:
        print("\nЗакрытие браузера...")
        driver.quit()
        print("Браузер успешно закрыт")
    except Exception as e:
        print(f"Не удалось закрыть браузер: {e}")