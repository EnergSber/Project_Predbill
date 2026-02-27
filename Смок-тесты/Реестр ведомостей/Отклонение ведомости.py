"""
ТЕСТОВЫЙ КЕЙС: Реестр ведомостей - Отклонение

ЦЕЛЬ: Проверка функциональности отклонения ведомостей в разделе "Реестр ведомостей"

ОПИСАНИЕ ТЕСТА:
1. Авторизация в системе под пользователем predbill
2. Переход в раздел "Реестр ведомостей"
3. Открытие фильтра и сброс перед заполнением
4. Выбор категорий (Tн.р. = 0, Tн.р. < 15 суток)
5. Выбор статусов (Отправлена, Не отправлена)
6. Применение фильтров
7. Отметка первых трех чекбоксов с проверкой активности кнопки "Действие"
8. Выбор опции "Отклонить" из меню действий
9. Выбор случайной причины отклонения
10. Проверка адресов в модальном окне
11. Сохранение и проверка успешности операции

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- Фильтры корректно применяются
- Ведомости успешно отклоняются с выбранной причиной
- Отсутствие ошибок в процессе выполнения теста
- Корректная работа всех элементов интерфейса

ОСОБЕННОСТИ:
- Используется универсальная функция поиска полей по тексту лейбла
- Подробное логирование каждого шага
- Проверка адресов в модальном окне
- Сохранение выбранных адресов для последующей проверки
- Циклический перебор строк при неактивной кнопке "Действие"
- Обработка ошибок на каждом этапе
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

# Глобальные переменные
saved_selected_addresses = []
table_selector = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body"
section_errors = []

# Настройка браузера
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()
wait = WebDriverWait(driver, 60)

# Данные для авторизации
from config import USERNAME, PASSWORD
URL = 'http://10.5.121.74/login'

print("=" * 60)
print("ТЕСТ РАЗДЕЛА: Реестр ведомостей - Отклонение")
print("=" * 60)


# ===================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====================

def add_error(error_text):
    if error_text not in section_errors:
        section_errors.append(error_text)
        print(f"ОШИБКА: {error_text}")


def press_tab():
    try:
        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB).perform()
        time.sleep(0.3)
        return True
    except Exception as e:
        print(f"Ошибка при нажатии Tab: {e}")
        return False


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


def click_svg_element(svg_selector, action_name):
    try:
        svg_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, svg_selector))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", svg_element)
        time.sleep(0.3)

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


# ===================== УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ПОИСКА ПОЛЕЙ =====================

def find_field_by_label(label_text, action_type="select", value=None, select_all=False):
    """
    УНИВЕРСАЛЬНАЯ ФУНКЦИЯ: ищет поле по тексту лейбла
    """
    try:
        print(f"\nИщем поле с лейблом: '{label_text}'")

        label_xpath = f"//label[contains(text(), '{label_text}')]"
        label = wait.until(EC.presence_of_element_located((By.XPATH, label_xpath)))
        print(f"  Лейбл найден")

        row = label.find_element(By.XPATH, "./ancestor::div[contains(@class, 'ant-row')]")

        if action_type == "input":
            try:
                element = row.find_element(By.CSS_SELECTOR, "input")
                print(f"  Нашли input поле")
            except:
                print(f"  Не нашли input поле")
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

        else:
            try:
                element = row.find_element(By.CSS_SELECTOR, "div.ant-select-selector")
            except:
                try:
                    element = row.find_element(By.CSS_SELECTOR, "div.ant-col.ant-col-14 > div > div > div")
                except:
                    print(f"  Не нашли кликабельный элемент")
                    return False

            print(f"  Нашли выпадающий список")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            element.click()
            print(f"  Открыли выпадающий список")
            time.sleep(1)

            dropdown_selector = ".ant-select-dropdown:not(.ant-select-dropdown-hidden)"
            dropdown = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, dropdown_selector)))
            options = dropdown.find_elements(By.CSS_SELECTOR, ".ant-select-item-option")
            print(f"  Найдено опций: {len(options)}")

            if not options:
                print(f"  Список пуст")
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
                return False
            else:
                valid_options = []
                for option in options:
                    try:
                        option_text = option.text.strip()
                        # Для категорий и статусов используем специальную логику
                        if label_text == "Категория":
                            target_categories = ["Tн.р. = 0", "Тн.р. = 0", "Tн.р. < 15 суток", "Тн.р. < 15 суток"]
                            for target in target_categories:
                                if option_text == target and option not in valid_options:
                                    valid_options.append(option)
                                    print(f"  Найдена нужная категория: '{option_text}'")
                        elif label_text == "Статус ведомости":
                            target_statuses = ["Отправлена", "Не отправлена"]
                            for target in target_statuses:
                                if option_text == target and option not in valid_options:
                                    valid_options.append(option)
                                    print(f"  Найден нужный статус: '{option_text}'")
                        else:
                            if "Выбрать все" not in option_text and option_text:
                                valid_options.append(option)
                    except:
                        continue

                if not valid_options:
                    print(f"  Нет доступных значений")
                    return False

                # Выбираем все найденные опции (для категорий и статусов может быть несколько)
                selected_count = 0
                for option in valid_options:
                    try:
                        option.click()
                        selected_count += 1
                        time.sleep(0.3)
                    except:
                        continue

                print(f"  Выбрано опций: {selected_count}")
                time.sleep(0.5)



                return True if selected_count > 0 else False

    except Exception as e:
        print(f"Ошибка при обработке поля '{label_text}': {e}")
        return False


# ===================== ФУНКЦИИ ДЛЯ РАБОТЫ С ТАБЛИЦЕЙ =====================

def verify_first_three_selected():
    try:
        print("\nПроверяем что отмечены первые три ведомости...")

        table_body = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, table_selector))
        )

        rows = table_body.find_elements(By.CSS_SELECTOR, "div.BaseTable__row")

        if len(rows) < 3:
            add_error(f"В таблице меньше 3 строк: {len(rows)}")
            return False

        first_three_selected = True
        for i in range(3):
            try:
                checkbox = rows[i].find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                if not checkbox.is_selected():
                    print(f"  Строка {i + 1}: НЕ отмечена!")
                    first_three_selected = False
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


def verify_selected_statements():
    try:
        print("\nПроверяем выбранные ведомости...")

        selected_addresses = []
        table_body = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, table_selector))
        )

        rows = table_body.find_elements(By.CSS_SELECTOR, "div.BaseTable__row")

        if len(rows) == 0:
            print("Таблица пуста")
            return False

        print(f"Найдено строк в таблице: {len(rows)}")

        check_rows = min(5, len(rows))
        print(f"Проверяем первые {check_rows} строк...")

        for i in range(check_rows):
            try:
                row = rows[i]
                checkbox = row.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                is_selected = checkbox.is_selected()

                cells = row.find_elements(By.CSS_SELECTOR, ".BaseTable__row-cell")

                if len(cells) >= 5:
                    address_cell = cells[4]
                    try:
                        address_element = address_cell.find_element(By.CSS_SELECTOR, "span.textEllipsis")
                        address = address_element.text.strip()
                    except:
                        address = address_cell.text.strip()
                        address = address.replace('\n', ' ')
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

        global saved_selected_addresses
        saved_selected_addresses = selected_addresses

        print("Отмеченные адреса сохранены для проверки")
        for i, addr in enumerate(selected_addresses, 1):
            print(f"  {i}. {addr}")

        return True
    except Exception as e:
        print(f"Ошибка при проверке ведомостей: {e}")
        return False


def mark_checkboxes():
    try:
        print("Отмечаем первые три чекбокса...")

        table_body = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, table_selector))
        )

        max_attempts = 10
        attempt = 0
        start_row = 0

        while attempt < max_attempts:
            print(f"\nПопытка {attempt + 1}: отмечаем строки {start_row + 1}-{start_row + 3}")

            rows = table_body.find_elements(By.CSS_SELECTOR, "div.BaseTable__row")

            if len(rows) < start_row + 3:
                print(f"Достигнут конец таблицы, всего строк: {len(rows)}")
                return False

            marked_count = 0
            marked_rows = []
            for i in range(start_row, start_row + 3):
                try:
                    checkbox = rows[i].find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                    time.sleep(0.3)

                    if not checkbox.is_selected():
                        checkbox.click()
                        print(f"  Отмечена строка {i + 1}")
                    else:
                        print(f"  Строка {i + 1} уже отмечена")

                    marked_count += 1
                    marked_rows.append(i)
                    time.sleep(0.2)
                except Exception as e:
                    print(f"  Ошибка при отметке строки {i + 1}: {e}")

            if marked_count < 3:
                print(f"Отмечено только {marked_count} из 3 строк")
                return False

            time.sleep(1)

            # Проверяем что кнопка "Действие" активна
            try:
                action_button = driver.find_element(By.CSS_SELECTOR,
                                                     "button.ant-btn.ant-btn-link.ant-dropdown-trigger.inlineButton")
                if action_button.is_enabled():
                    print(f"✅ Кнопка 'Действие' активна на попытке {attempt + 1}")
                    return True
                else:
                    print(f"⚠️ Кнопка 'Действие' неактивна, снимаем отметки и пробуем следующие строки")

                    for i in marked_rows:
                        try:
                            checkbox = rows[i].find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                            if checkbox.is_selected():
                                checkbox.click()
                                print(f"  Снята отметка со строки {i + 1}")
                                time.sleep(0.2)
                        except:
                            continue

                    start_row += 3
                    attempt += 1
            except Exception as e:
                print(f"Ошибка при проверке кнопки 'Действие': {e}")
                return False

        print(f"❌ Не удалось найти активную кнопку 'Действие' после {max_attempts} попыток")
        return False
    except Exception as e:
        add_error(f"Ошибка при отметке чекбоксов: {e}")
        return False


# ===================== ФУНКЦИИ ДЛЯ РАБОТЫ С ДЕЙСТВИЯМИ =====================

def click_action_button():
    try:
        print("Кликаем на кнопку 'Действие'...")

        action_button = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.ant-btn.ant-btn-link.ant-dropdown-trigger.inlineButton"))
        )

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", action_button)
        time.sleep(0.5)
        action_button.click()
        print("Кнопка 'Действие' нажата")
        time.sleep(1)

        return True
    except Exception as e:
        add_error(f"Ошибка при клике на кнопку 'Действие': {e}")
        return False


def select_reject_option():
    try:
        print("Выбираем опцию 'Отклонить'...")

        reject_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Отклонить')]")

        for element in reject_elements:
            try:
                if element.is_displayed() and element.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.5)
                    element.click()
                    print("Опция 'Отклонить' выбрана")
                    time.sleep(1)

                    check_and_close_errors("После выбора 'Отклонить'")
                    return True
            except:
                continue

        add_error("Не найден элемент 'Отклонить'")
        return False
    except Exception as e:
        add_error(f"Ошибка при выборе опции 'Отклонить': {e}")
        return False


def select_reject_reason():
    try:
        print("Выбираем причину отклонения...")
        time.sleep(2)

        reason_container_selector = "#addRolesModalForm > div.rt-form-body > div.flexBetween > div > div > div.ant-col.ant-col-28.ant-form-item-control > div > div > div > div"

        reason_container = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, reason_container_selector))
        )

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reason_container)
        time.sleep(0.5)
        print("Нашли контейнер поля причины")

        try:
            open_dropdown = driver.find_element(By.CSS_SELECTOR, ".ant-select-dropdown:not(.ant-select-dropdown-hidden)")
            print("Выпадающий список уже открыт")
        except:
            print("Кликаем чтобы открыть список причин...")
            reason_container.click()
            time.sleep(1)

        try:
            time.sleep(1.5)
            reason_list = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".ant-select-dropdown:not(.ant-select-dropdown-hidden)"))
            )
            print("Выпадающий список причин найден")
        except Exception as e:
            print(f"Не видим выпадающий список: {e}")
            reason_container.click()
            time.sleep(1.5)
            reason_list = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".ant-select-dropdown:not(.ant-select-dropdown-hidden)"))
            )
            print("Выпадающий список появился после повторного клика")

        reason_options = reason_list.find_elements(By.CSS_SELECTOR, ".ant-select-item-option")

        if not reason_options:
            reason_options = reason_list.find_elements(By.CSS_SELECTOR, "div[role='option']")
            reason_options = reason_list.find_elements(By.CSS_SELECTOR, "div.ant-select-item")

        if not reason_options:
            add_error("Список причин пуст")
            return False

        print(f"Найдено причин для выбора: {len(reason_options)}")

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

        random_option = random.choice(valid_options)
        reason_text = random_option.text.strip()

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", random_option)
        time.sleep(0.3)
        random_option.click()
        print(f"Выбрана причина: '{reason_text}'")
        time.sleep(0.5)

        check_and_close_errors("После выбора причины")
        return True
    except Exception as e:
        add_error(f"Ошибка при выборе причины: {e}")
        return False


def click_save_button():
    try:
        print("Нажимаем кнопку 'Сохранить'...")
        time.sleep(2)

        try:
            save_button = driver.find_element(By.CSS_SELECTOR,
                                              "#addRolesModalForm > div.rt-form-footer > button.ant-btn.ant-btn-primary.ml-s")
            if save_button.is_displayed() and save_button.is_enabled():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_button)
                time.sleep(0.5)
                save_button.click()
                print("Кнопка 'Сохранить' нажата")
                time.sleep(2)
                check_and_close_errors("После нажатия 'Сохранить'")
                return True
        except:
            pass

        save_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Сохранить')]")

        for button in save_buttons:
            try:
                if button.is_displayed() and button.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    time.sleep(0.5)
                    button.click()
                    print("Кнопка 'Сохранить' нажата (по тексту)")
                    time.sleep(2)
                    check_and_close_errors("После нажатия 'Сохранить'")
                    return True
            except:
                continue

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


# ===================== ФУНКЦИИ ДЛЯ ПРОВЕРКИ МОДАЛЬНОГО ОКНА =====================

def verify_addresses_in_modal():
    try:
        print("\nПроверяем адреса в модальном окне...")
        time.sleep(2)

        try:
            modal = driver.find_element(By.CSS_SELECTOR, ".ant-modal")
            modal_html = modal.get_attribute('outerHTML')
            print(f"  HTML модального окна (первые 500 символов): {modal_html[:500]}...")
        except:
            print("  Не удалось получить HTML модального окна")

        try:
            modal_body = driver.find_element(By.CSS_SELECTOR, ".ant-modal-body")
            modal_text = modal_body.text
            print(f"  Текст модального окна:\n{modal_text}")

            lines = [line.strip() for line in modal_text.split('\n') if line.strip()]
            print(f"  Найдено {len(lines)} строк в модальном окне:")

            addresses_in_modal = []
            for line in lines:
                if any(keyword in line.lower() for keyword in ['ул.', 'д.', 'просп.', 'бульв.', 'шоссе', 'пер.']):
                    addresses_in_modal.append(line)

            global saved_selected_addresses

            print(f"\nСохраненные адреса (из таблицы):")
            for i, addr in enumerate(saved_selected_addresses, 1):
                print(f"  {i}. {addr}")

            print(f"\nНайденные адреса в модальном окне:")
            for i, addr in enumerate(addresses_in_modal, 1):
                print(f"  {i}. {addr}")

            if not saved_selected_addresses:
                print("  ВНИМАНИЕ: Нет сохраненных адресов для сравнения")
                return False

            if not addresses_in_modal:
                print("  ВНИМАНИЕ: Не найдены адреса в модальном окне")
                return False

            matches_found = 0
            for saved_addr in saved_selected_addresses:
                found = False
                saved_key_parts = saved_addr.split(',')[0]

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


def apply_filters():
    try:
        print("Применяем фильтры...")

        apply_button_selector = "button[section='billingStatements'] span[role='img'][aria-label='check']"

        apply_svg = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, apply_button_selector))
        )

        parent_button = apply_svg.find_element(By.XPATH, "..")
        parent_button.click()
        print("Фильтры применены")

        wait_for_page_load()
        check_and_close_errors("После применения фильтров")

        return True
    except Exception as e:
        add_error(f"Ошибка при применении фильтров: {e}")
        return False


# ===================== ОСНОВНОЙ КОД =====================

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
    check_and_close_errors("После перехода в раздел")

    # 3. ОТКРЫТИЕ ФИЛЬТРА
    print("\n" + "=" * 50)
    print("ШАГ 3: ОТКРЫТИЕ ФИЛЬТРА")
    print("=" * 50)

    if not click_svg_element("svg[data-icon='filter']", "Фильтр открыт"):
        raise Exception("Не удалось открыть фильтр")
    time.sleep(2)
    check_and_close_errors("После открытия фильтра")

    # 4. СБРОС ФИЛЬТРОВ
    print("\n" + "=" * 50)
    print("ШАГ 4: СБРОС ФИЛЬТРОВ")
    print("=" * 50)

    if not click_svg_element("svg[data-icon='stop']", "Фильтры сброшены"):
        print("Предупреждение: не удалось сбросить фильтры")
    time.sleep(1)
    wait_for_page_load()
    check_and_close_errors("После сброса фильтров")

    # 5. УСТАНОВКА КАТЕГОРИЙ
    print("\n" + "=" * 50)
    print("ШАГ 5: УСТАНОВКА КАТЕГОРИЙ")
    print("=" * 50)

    if not find_field_by_label("Категория"):
        add_error("Не удалось установить категории")
    press_tab()
    check_and_close_errors("После установки категорий")

    # 6. УСТАНОВКА СТАТУСОВ
    print("\n" + "=" * 50)
    print("ШАГ 6: УСТАНОВКА СТАТУСОВ")
    print("=" * 50)

    if not find_field_by_label("Статус ведомости"):
        add_error("Не удалось установить статусы")
    press_tab()
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

    # 12. ПРОВЕРКА ВЫБРАННЫХ ВЕДОМОСТЕЙ
    print("\n" + "=" * 50)
    print("ШАГ 12: ПРОВЕРКА ВЫБРАННЫХ ВЕДОМОСТЕЙ")
    print("=" * 50)

    if not verify_first_three_selected():
        add_error("Не все первые три ведомости отмечены")
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

    check_and_close_errors("Финальная проверка")

    success_found = False
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
        try:
            table_body = driver.find_element(By.CSS_SELECTOR, table_selector)
            rows = table_body.find_elements(By.CSS_SELECTOR, "div.BaseTable__row")

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

    check_and_close_errors("Финальная проверка")

    # ИТОГОВЫЙ ОТЧЕТ
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
    try:
        print("\nЗакрытие браузера...")
        driver.quit()
        print("Браузер успешно закрыт")
    except Exception as e:
        print(f"Не удалось закрыть браузер: {e}")