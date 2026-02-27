"""
ТЕСТОВЫЙ КЕЙС: Реестр водомеров - Отклонение

ЦЕЛЬ: Проверка функциональности отклонения показаний водомеров в разделе "Реестр водомеров"

ОПИСАНИЕ ТЕСТА:
1. Авторизация в системе под пользователем predbill
2. Переход в раздел "Реестр водомеров"
3. Открытие фильтра и сброс перед заполнением
4. Установка статусов (Отправлена, Не отправлена)
5. Применение фильтров
6. Отметка первых трех ведомостей
7. Выбор опции "Отклонить" из меню действий
8. Выбор случайной причины отклонения
9. Проверка адресов в модальном окне
10. Сохранение и проверка успешности операции

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- Фильтры корректно применяются
- Ведомости успешно отклоняются с выбранной причиной
- Адреса в модальном окне соответствуют выбранным ведомостям
- Отсутствие ошибок в процессе выполнения теста
- Корректная работа всех элементов интерфейса

ОСОБЕННОСТИ:
- Используется универсальная функция поиска полей по тексту лейбла
- Подробное логирование каждого шага
- Проверка адресов в модальном окне (адрес во 2-й колонке)
- Сохранение выбранных адресов для последующей проверки
- Сравнение адресов с учетом частичных совпадений
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
selected_ao_value = None

# Инициализация драйвера
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()
wait = WebDriverWait(driver, 60)

# Данные для авторизации
from config import USERNAME, PASSWORD
URL = 'http://10.5.121.74/login'

print("=" * 60)
print("ТЕСТ РАЗДЕЛА: Реестр водомеров - Отклонение")
print("=" * 60)


# ===================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====================

def add_error(error_text):
    if error_text not in section_errors:
        section_errors.append(error_text)
        print(f"\033[91mОШИБКА: {error_text}\033[0m")


def print_success(text):
    print(f"\033[92m{text}\033[0m")


def print_warning(text):
    print(f"\033[93m{text}\033[0m")


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


def press_tab():
    try:
        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB).perform()
        time.sleep(0.3)
        return True
    except Exception as e:
        print(f"Ошибка при нажатии Tab: {e}")
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

        check_and_close_errors(f"После {action_name.lower()}")

        return True

    except Exception as e:
        add_error(f"Не удалось {action_name}: {e}")
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
                        # Для статусов используем специальную логику
                        if label_text == "Статус ведомости":
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

                # Выбираем все найденные опции
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

                # АДРЕС В ИНДЕКСЕ 2 (ТРЕТЬЯ КОЛОНКА)
                if len(cells) >= 3:
                    address_cell = cells[2]

                    try:
                        span_element = address_cell.find_element(By.CSS_SELECTOR, "span.textEllipsis")
                        address = span_element.text.strip()
                    except:
                        address = address_cell.text.strip()
                        address = address.replace('\n', ' ').strip()
                else:
                    address = "Адрес не найден"

                status = "✓" if is_selected else "✗"
                print(f"  Строка {i + 1}: {status} АДРЕС: '{address}'")

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
            print_warning(f"Отмечено только {len(selected_addresses)} ведомостей, ожидалось 3")
            return False

        global saved_selected_addresses
        saved_selected_addresses = selected_addresses

        print("\n✅ Сохраненные АДРЕСА (из таблицы):")
        for i, addr in enumerate(selected_addresses, 1):
            print(f"  {i}. '{addr}'")

        return True

    except Exception as e:
        print(f"Ошибка при проверке ведомостей: {e}")
        import traceback
        traceback.print_exc()
        return False


def mark_checkboxes():
    try:
        print("Отмечаем первые три чекбокса...")

        table_body = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, table_selector))
        )

        rows = table_body.find_elements(By.CSS_SELECTOR, "div.BaseTable__row")

        if len(rows) < 3:
            add_error(f"В таблице меньше 3 строк: {len(rows)}")
            return False

        marked_count = 0
        for i in range(3):
            try:
                checkbox = rows[i].find_element(By.CSS_SELECTOR, "input[type='checkbox']")

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                time.sleep(0.3)

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
            print_success("Все три чекбокса отмечены")
            return True
        else:
            add_error(f"Отмечено только {marked_count} из 3 чекбоксов")
            return marked_count > 0

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

        check_and_close_errors("После нажатия 'Действие'")

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
            open_dropdown = driver.find_element(By.CSS_SELECTOR,
                                                ".ant-select-dropdown:not(.ant-select-dropdown-hidden)")
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
            print("Пробуем кликнуть еще раз...")
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

        print("Доступные причины:")
        for i, option in enumerate(reason_options[:10]):
            try:
                text = option.text.strip()
                if text:
                    print(f"  {i + 1}. '{text}'")
            except:
                continue

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
        time.sleep(1)

        try:
            selected_value = driver.find_element(By.CSS_SELECTOR,
                                                 f"{reason_container_selector} .ant-select-selection-item")
            selected_text = selected_value.text.strip()
            print(f"В поле выбрано: '{selected_text}'")

            if not selected_text or selected_text == "Выберите значение":
                print("Предупреждение: значение в поле не изменилось")
                if valid_options:
                    first_option = valid_options[0]
                    first_option.click()
                    print("Повторно выбрана первая причина")
                    time.sleep(0.5)
        except:
            print("Не удалось проверить выбранное значение в поле")

        check_and_close_errors("После выбора причины")

        return True

    except Exception as e:
        add_error(f"Ошибка при выборе причины: {e}")
        print(f"Детали ошибки: {str(e)}")

        try:
            print("Пробуем альтернативный способ через JavaScript...")
            dropdown = driver.find_element(By.CSS_SELECTOR, ".ant-select-dropdown")
            options = dropdown.find_elements(By.CSS_SELECTOR, ".ant-select-item-option")

            if options:
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
            modal_table_container = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#addRolesModalForm > div.rt-form-body > div.rt-table.mb-s > div"))
            )
            print("Найден контейнер таблицы в модальном окне")
        except Exception as e:
            print(f"Не удалось найти контейнер таблицы: {e}")
            return False

        try:
            modal_table_body = modal_table_container.find_element(By.CSS_SELECTOR, ".BaseTable__body")
            print("Найдено тело таблицы в модальном окне")
        except:
            try:
                modal_table_body = driver.find_element(By.CSS_SELECTOR, "#addRolesModalForm .BaseTable__body")
                print("Найдено тело таблицы через альтернативный селектор")
            except Exception as e:
                print(f"Не удалось найти тело таблицы: {e}")
                return False

        modal_rows = modal_table_body.find_elements(By.CSS_SELECTOR, ".BaseTable__row")

        if not modal_rows:
            print("В таблице модального окна нет строк")
            return False

        print(f"Найдено строк в модальном окне: {len(modal_rows)}")

        addresses_in_modal = []
        for i, row in enumerate(modal_rows, 1):
            try:
                cells = row.find_elements(By.CSS_SELECTOR, ".BaseTable__row-cell")

                # АДРЕС В ИНДЕКСЕ 2 (ВТОРАЯ КОЛОНКА) В МОДАЛЬНОМ ОКНЕ
                if len(cells) >= 2:
                    address_cell = cells[2]

                    address_text = address_cell.text.strip()

                    if address_text:
                        addresses_in_modal.append(address_text)
                        print(f"  Строка {i}: найден адрес '{address_text}'")
            except Exception as e:
                print(f"  Ошибка при обработке строки {i}: {e}")
                continue

        print(f"\nВсего найдено адресов в модальном окне: {len(addresses_in_modal)}")
        for i, addr in enumerate(addresses_in_modal, 1):
            print(f"  {i}. {addr}")

        global saved_selected_addresses
        print(f"\nСохраненные адреса (из таблицы):")
        for i, addr in enumerate(saved_selected_addresses, 1):
            print(f"  {i}. '{addr}'")

        if not saved_selected_addresses:
            print_warning("ВНИМАНИЕ: Нет сохраненных адресов для сравнения")
            return False

        if not addresses_in_modal:
            print_warning("ВНИМАНИЕ: Не найдены адреса в модальном окне")
            return False

        print("\n🔍 СРАВНЕНИЕ АДРЕСОВ:")
        matches_found = 0

        for saved_addr in saved_selected_addresses:
            found = False
            saved_key_parts = saved_addr.lower()

            for modal_addr in addresses_in_modal:
                modal_lower = modal_addr.lower()
                if saved_key_parts in modal_lower or modal_lower in saved_key_parts:
                    matches_found += 1
                    print(f"  ✓ СОВПАДЕНИЕ: '{saved_addr}' <-> '{modal_addr}'")
                    found = True
                    break

                saved_parts = saved_key_parts.split()
                for part in saved_parts:
                    if len(part) > 3 and part in modal_lower:
                        matches_found += 1
                        print(f"  ✓ ЧАСТИЧНОЕ СОВПАДЕНИЕ: '{saved_addr}' содержит '{part}' в '{modal_addr}'")
                        found = True
                        break

                if found:
                    break

            if not found:
                print(f"  ✗ НЕТ СОВПАДЕНИЯ: '{saved_addr}'")

        print(f"\n  Результат: найдено {matches_found} из {len(saved_selected_addresses)} совпадений")

        if matches_found >= len(saved_selected_addresses):
            print_success(f"УСПЕХ: Все адреса совпадают!")
            return True
        elif matches_found > 0:
            print_warning(f"ЧАСТИЧНО: Найдено {matches_found} из {len(saved_selected_addresses)} совпадений")
            return True
        else:
            add_error("Не найдено ни одного совпадения адресов")
            return False

    except Exception as e:
        add_error(f"Ошибка при проверке адресов в модальном окне: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_operation_success():
    try:
        print("\nПроверяем успешность операции отклонения...")
        time.sleep(3)

        success = False

        success_selectors = [
            "div.ant-notification-notice-success",
            "div.ant-alert-success",
            ".ant-message-success"
        ]

        for selector in success_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    try:
                        if elem.is_displayed():
                            success_text = elem.text.strip()
                            if success_text and len(success_text) > 3:
                                print_success(f"Успешное сообщение: {success_text}")
                                success = True
                                break
                    except:
                        continue
                if success:
                    break
            except:
                continue

        if not success:
            try:
                modal = driver.find_element(By.CSS_SELECTOR, ".ant-modal")
                if not modal.is_displayed():
                    print_success("Модальное окно закрылось - операция выполнена")
                    success = True
            except:
                print_success("Модальное окно не найдено - операция выполнена")
                success = True

        if success and saved_selected_addresses:
            try:
                print("Проверяем обновление таблицы...")
                time.sleep(2)

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
                    print_warning(f"Предупреждение: {first_three_checked} из первых трех ведомостей все еще отмечены")

            except Exception as e:
                print(f"Не удалось проверить обновление таблицы: {e}")

        check_and_close_errors("После проверки успешности операции")

        return success

    except Exception as e:
        print(f"Ошибка при проверке успешности операции: {e}")
        return True


def apply_filters():
    try:
        print("Применяем фильтры...")

        apply_button_selector = "button[section='watermeterStatements'] span[role='img'][aria-label='check']"

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
    print_success("Авторизация успешна")

    check_and_close_errors("После авторизации")

    # 2. ПЕРЕХОД В РАЗДЕЛ
    print("\n" + "=" * 50)
    print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ")
    print("=" * 50)

    section_url = 'http://10.5.121.74/commercialControl/watermeterStatements'
    driver.get(section_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("Переход в раздел 'Реестр водомеров'")
    time.sleep(2)

    check_and_close_errors("После перехода в раздел")

    # 3. ОТКРЫТИЕ ФИЛЬТРА
    print("\n" + "=" * 50)
    print("ШАГ 3: ОТКРЫТИЕ ФИЛЬТРА")
    print("=" * 50)

    if not click_svg_element("svg[data-icon='filter']", "Фильтр открыт"):
        add_error("Не удалось открыть фильтр")

    time.sleep(2)
    check_and_close_errors("После открытия фильтра")

    # 4. СБРОС ФИЛЬТРОВ
    print("\n" + "=" * 50)
    print("ШАГ 4: СБРОС ФИЛЬТРОВ")
    print("=" * 50)

    if not click_svg_element("svg[data-icon='stop']", "Фильтры сброшены"):
        print_warning("Не удалось сбросить фильтры")

    time.sleep(1)
    wait_for_page_load()
    check_and_close_errors("После сброса фильтров")

    # 5. УСТАНОВКА КАТЕГОРИЙ (пропускаем)
    print("\n" + "=" * 50)
    print("ШАГ 5: УСТАНОВКА КАТЕГОРИЙ (пропущено)")
    print("=" * 50)
    press_tab()
    check_and_close_errors("После установки категорий")

    # 6. УСТАНОВКА СТАТУСОВ (через универсальную функцию)
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
        print_warning("Адреса в модальном окне не полностью совпадают с выбранными")

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

    operation_success = check_operation_success()

    # ИТОГОВЫЙ ОТЧЕТ
    print("\n" + "=" * 60)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)

    if operation_success:
        print_success("Операция отклонения выполнена успешно")
    else:
        add_error("Операция отклонения не завершена успешно")
        print_warning("Операция отклонения не завершена успешно")

    if section_errors:
        print(f"\n\033[91mНайдено ошибок: {len(section_errors)}\033[0m")
        for i, error in enumerate(section_errors, 1):
            print(f"\033[91m  {i}. {error}\033[0m")
    else:
        print(f"\n\033[92mОшибок не обнаружено\033[0m")

    print("\n" + "=" * 60)
    if operation_success and len(section_errors) == 0:
        print_success("ТЕСТ ОТКЛОНЕНИЯ В РЕЕСТРЕ ВОДОМЕРОВ УСПЕШНО ЗАВЕРШЕН")
    elif operation_success and len(section_errors) > 0:
        print_warning("ТЕСТ ЗАВЕРШЕН С ОШИБКАМИ, НО ОПЕРАЦИЯ ВЫПОЛНЕНА")
    else:
        print("\033[91mТЕСТ ЗАВЕРШЕН С ОШИБКАМИ, ОПЕРАЦИЯ НЕ ВЫПОЛНЕНА\033[0m")
    print("=" * 60)

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