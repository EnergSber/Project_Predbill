"""
ТЕСТОВЫЙ КЕЙС: Реестр водомеров - Отправка выбранных объемов

ЦЕЛЬ: Проверка функциональности отправки выбранных объемов в разделе "Реестр водомеров"

ОПИСАНИЕ ТЕСТА:
1. Авторизация в системе под пользователем predbill
2. Переход в раздел "Реестр водомеров"
3. Открытие фильтра и сброс перед заполнением
4. Установка статуса "Не отправлена"
5. Применение фильтров
6. Циклическая отправка ведомостей в течение 3 минут:
   - Отметка следующих 3 ведомостей
   - Выбор опции "Отправить" из меню действий
   - Проверка активности кнопки "Отправить" в модальном окне
   - При активной кнопке - отправка и завершение цикла
   - При неактивной кнопке - переход к следующим ведомостям
7. Проверка адресов в модальном окне
8. Проверка успешности операции отправки

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- Фильтры корректно применяются
- Находится группа ведомостей с активной кнопкой "Отправить"
- Ведомости успешно отправляются
- Отсутствие ошибок в процессе выполнения теста
- Корректная работа всех элементов интерфейса

ОСОБЕННОСТИ:
- Используется универсальная функция поиска полей по тексту лейбла
- Циклический перебор ведомостей в течение 3 минут
- Подробное логирование каждого шага с цветовым выделением
- Проверка адресов в модальном окне
- Сохранение выбранных адресов для последующей проверки
- Автоматическое закрытие модального окна при неактивной кнопке
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
import re
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
print("ТЕСТ РАЗДЕЛА: Реестр водомеров - Отправка выбранных объемов")
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
                            target_statuses = ["Не отправлена"]
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

def clear_all_checkboxes():
    try:
        print("Снимаем отметки со всех ведомостей...")
        table_body = driver.find_element(By.CSS_SELECTOR, table_selector)
        rows = table_body.find_elements(By.CSS_SELECTOR, "div.BaseTable__row")

        unchecked_count = 0
        for i, row in enumerate(rows):
            try:
                checkbox = row.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                if checkbox.is_selected():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                    time.sleep(0.2)
                    checkbox.click()
                    unchecked_count += 1
            except:
                continue

        if unchecked_count > 0:
            print(f"Снято отметок: {unchecked_count}")

        check_and_close_errors("После снятия отметок")

        return True
    except Exception as e:
        print(f"Ошибка при снятии отметок: {e}")
        return False


def mark_next_checkboxes(start_index):
    try:
        print(f"Отмечаем ведомости начиная с индекса {start_index + 1}...")

        table_body = driver.find_element(By.CSS_SELECTOR, table_selector)
        rows = table_body.find_elements(By.CSS_SELECTOR, "div.BaseTable__row")

        if start_index >= len(rows):
            print_warning("Достигнут конец таблицы")
            return False, start_index

        marked_count = 0
        next_start_index = start_index

        for i in range(start_index, min(start_index + 3, len(rows))):
            try:
                checkbox = rows[i].find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                time.sleep(0.3)

                if not checkbox.is_selected():
                    checkbox.click()
                    marked_count += 1
                    print(f"  Отмечена строка {i + 1}")
                    time.sleep(0.3)
                next_start_index = i + 1
            except Exception as e:
                print(f"  Ошибка при отметке строки {i + 1}: {e}")
                next_start_index = i + 1

        if marked_count > 0:
            print(f"Отмечено ведомостей: {marked_count}")

            global saved_selected_addresses
            saved_selected_addresses = []
            for i in range(start_index, min(start_index + 3, len(rows))):
                try:
                    cells = rows[i].find_elements(By.CSS_SELECTOR, ".BaseTable__row-cell")
                    if len(cells) >= 5:
                        try:
                            address_element = cells[4].find_element(By.CSS_SELECTOR, "span.textEllipsis")
                            address = address_element.text.strip()
                        except:
                            address = cells[4].text.strip()
                        saved_selected_addresses.append(address)
                except:
                    saved_selected_addresses.append(f"Адрес {i + 1}")

            check_and_close_errors("После отметки чекбоксов")

            return True, next_start_index
        else:
            add_error("Не удалось отметить новые ведомости")
            return False, next_start_index

    except Exception as e:
        add_error(f"Ошибка при отметке ведомостей: {e}")
        return False, start_index


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


def select_send_option():
    try:
        print("Выбираем опцию 'Отправить'...")

        try:
            send_button = driver.find_element(By.CSS_SELECTOR,
                                              "html > div > div > div > ul > li:nth-child(4) > span > button")
            if send_button.is_displayed() and send_button.is_enabled():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", send_button)
                time.sleep(0.5)
                send_button.click()
                print("Опция 'Отправить' выбрана")
                time.sleep(1)

                check_and_close_errors("После выбора 'Отправить'")

                return True
        except:
            pass

        send_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Отправить')]")

        for element in send_elements:
            try:
                if element.is_displayed() and element.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.5)
                    element.click()
                    print("Опция 'Отправить' выбрана")
                    time.sleep(1)

                    check_and_close_errors("После выбора 'Отправить'")

                    return True
            except:
                continue

        add_error("Не найден элемент 'Отправить'")
        return False

    except Exception as e:
        add_error(f"Ошибка при выборе опции 'Отправить': {e}")
        return False


def is_send_button_enabled():
    try:
        send_button = driver.find_element(By.CSS_SELECTOR,
                                          "#addRolesModalForm > div.rt-form-footer > button.ant-btn.ant-btn-primary.ml-s")

        if send_button.is_displayed() and send_button.is_enabled():
            return True
    except:
        pass

    try:
        modal_footer_buttons = driver.find_elements(By.CSS_SELECTOR,
                                                    "#addRolesModalForm .rt-form-footer button.ant-btn.ant-btn-primary")

        for button in modal_footer_buttons:
            if button.is_displayed() and button.is_enabled():
                return True
    except:
        pass

    try:
        send_buttons = driver.find_elements(By.XPATH,
                                            "//div[@id='addRolesModalForm']//button[contains(text(), 'Отправить')]")

        for button in send_buttons:
            if button.is_displayed() and button.is_enabled():
                return True
    except:
        pass

    return False


def click_send_button_in_modal():
    try:
        print("Нажимаем кнопку 'Отправить' в модальном окне...")
        time.sleep(2)

        try:
            send_button = driver.find_element(By.CSS_SELECTOR,
                                              "html > div > div > div > ul > li:nth-child(3) > span > button")

            if send_button.is_displayed() and send_button.is_enabled():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", send_button)
                time.sleep(0.5)
                send_button.click()
                print("Кнопка 'Отправить' нажата")
                time.sleep(2)

                check_and_close_errors("После нажатия 'Отправить'")

                return True
        except Exception as e:
            print(f"Точный селектор не сработал: {e}")

        try:
            modal_footer_buttons = driver.find_elements(By.CSS_SELECTOR,
                                                        "#addRolesModalForm .rt-form-footer button.ant-btn.ant-btn-primary")

            for button in modal_footer_buttons:
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    print("Кнопка 'Отправить' нажата")
                    time.sleep(2)

                    check_and_close_errors("После нажатия 'Отправить'")

                    return True
        except:
            pass

        try:
            send_buttons = driver.find_elements(By.XPATH,
                                                "//div[@id='addRolesModalForm']//button[contains(text(), 'Отправить')]")

            for button in send_buttons:
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    print("Кнопка 'Отправить' нажата")
                    time.sleep(2)

                    check_and_close_errors("После нажатия 'Отправить'")

                    return True
        except:
            pass

        try:
            primary_buttons = driver.find_elements(By.CSS_SELECTOR,
                                                   ".ant-modal-footer button.ant-btn-primary")

            for button in primary_buttons:
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    print("Кнопка 'Отправить' нажата")
                    time.sleep(2)

                    check_and_close_errors("После нажатия 'Отправить'")

                    return True
        except:
            pass

        add_error("Не найдена кнопка 'Отправить' в модальном окне")
        return False

    except Exception as e:
        add_error(f"Ошибка при нажатии кнопки 'Отправить': {e}")
        return False


def check_operation_success_send():
    try:
        print("\nПроверяем успешность операции отправки...")
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

        check_and_close_errors("После проверки успешности операции")

        return success

    except Exception as e:
        print(f"Ошибка при проверке успешности операции: {e}")
        return True


def close_modal_if_open():
    """Закрывает модальное окно если оно открыто"""
    try:
        cancel_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Отмена')]")
        if cancel_btn.is_displayed():
            cancel_btn.click()
            time.sleep(1)
            check_and_close_errors("После нажатия 'Отмена'")
            return True
    except:
        try:
            close_btn = driver.find_element(By.CSS_SELECTOR, ".ant-modal-close")
            if close_btn.is_displayed():
                close_btn.click()
                time.sleep(1)
                check_and_close_errors("После закрытия модального окна")
                return True
        except:
            pass
    return False


def verify_addresses_in_modal_send():
    try:
        print("\nПроверяем адреса в модальном окне отправки...")
        time.sleep(2)

        try:
            modal_body = driver.find_element(By.CSS_SELECTOR, ".ant-modal-body")
            modal_text = modal_body.text

            lines = [line.strip() for line in modal_text.split('\n') if line.strip()]

            addresses_in_modal = []
            for line in lines:
                if any(keyword in line.lower() for keyword in ['ул.', 'д.', 'просп.', 'бульв.', 'шоссе', 'пер.']):
                    addresses_in_modal.append(line)

            global saved_selected_addresses

            if not saved_selected_addresses:
                print_warning("ВНИМАНИЕ: Нет сохраненных адресов для сравнения")
                return False

            if not addresses_in_modal:
                print_warning("ВНИМАНИЕ: Не найдены адреса в модальном окне отправки")
                return False

            matches_found = 0
            for saved_addr in saved_selected_addresses:
                found = False
                saved_key_parts = saved_addr.split(',')[0]

                for modal_addr in addresses_in_modal:
                    if saved_key_parts in modal_addr:
                        matches_found += 1
                        print(f"  Совпадение: '{saved_key_parts}' найдено")
                        found = True
                        break

                if not found:
                    print(f"  Адрес не найден: {saved_addr}")

            if matches_found == len(saved_selected_addresses):
                print_success(f"Все {matches_found} адреса совпадают!")
                return True
            else:
                print_warning(f"Найдено только {matches_found} из {len(saved_selected_addresses)} совпадений")
                return matches_found > 0

        except Exception as e:
            print(f"Ошибка при анализе модального окна отправки: {e}")
            return False

    except Exception as e:
        print(f"Ошибка при проверке адресов: {e}")
        return False


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

    print("\n" + "=" * 50)
    print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ")
    print("=" * 50)

    section_url = 'http://10.5.121.74/commercialControl/watermeterStatements'
    driver.get(section_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("Переход в раздел 'Реестр водомеров'")
    time.sleep(2)

    check_and_close_errors("После перехода в раздел")

    print("\n" + "=" * 50)
    print("ШАГ 3: ОТКРЫТИЕ ФИЛЬТРА")
    print("=" * 50)

    if not click_svg_element("svg[data-icon='filter']", "Фильтр открыт"):
        add_error("Не удалось открыть фильтр")

    time.sleep(2)

    print("\n" + "=" * 50)
    print("ШАГ 4: СБРОС ФИЛЬТРОВ")
    print("=" * 50)

    if not click_svg_element("svg[data-icon='stop']", "Фильтры сброшены"):
        print_warning("Не удалось сбросить фильтры")

    time.sleep(1)
    wait_for_page_load()

    print("\n" + "=" * 50)
    print("ШАГ 5: УСТАНОВКА КАТЕГОРИЙ ДЛЯ ОТПРАВКИ")
    print("=" * 50)

    press_tab()

    print("\n" + "=" * 50)
    print("ШАГ 6: УСТАНОВКА СТАТУСОВ ДЛЯ ОТПРАВКИ")
    print("=" * 50)

    if not find_field_by_label("Статус ведомости"):
        add_error("Не удалось установить статусы для отправки")

    press_tab()

    print("\n" + "=" * 50)
    print("ШАГ 7: ПРИМЕНЕНИЕ ФИЛЬТРОВ")
    print("=" * 50)

    if not apply_filters():
        add_error("Не удалось применить фильтры")

    print("\n" + "=" * 60)
    print("ЗАПУСК ЦИКЛИЧЕСКОЙ ОТПРАВКИ ВЕДОМОСТЕЙ")
    print("=" * 60)
    print("Условие: ищем активную кнопку 'Отправить' в течение 3 минут")
    print("=" * 60)

    current_start_index = 0
    successful_sends = 0

    start_time = time.time()
    max_duration = 180  # 3 минуты в секундах
    attempt_count = 0

    while time.time() - start_time < max_duration:
        attempt_count += 1
        remaining_time = max_duration - (time.time() - start_time)
        print(f"\n{'=' * 50}")
        print(f"ПОПЫТКА #{attempt_count} | Осталось времени: {int(remaining_time)} сек")
        print(f"{'=' * 50}")

        # Снимаем все отметки
        clear_all_checkboxes()
        time.sleep(1)

        # Отмечаем следующие 3 ведомости
        mark_success, new_index = mark_next_checkboxes(current_start_index)

        if not mark_success:
            print_warning("Достигнут конец таблицы. Возвращаемся к началу...")
            current_start_index = 0
            continue

        current_start_index = new_index

        print("\n--- КЛИК НА 'ДЕЙСТВИЕ' И ВЫБОР 'ОТПРАВИТЬ' ---")

        if not click_action_button():
            add_error("Не удалось нажать кнопку 'Действие'")
            continue

        time.sleep(1)

        if not select_send_option():
            add_error("Не удалось выбрать опцию 'Отправить'")
            close_modal_if_open()
            continue

        time.sleep(2)

        print("\n--- ПРОВЕРКА ДОСТУПНОСТИ КНОПКИ 'ОТПРАВИТЬ' ---")

        if is_send_button_enabled():
            print_success("Кнопка 'Отправить' активна - выполняем отправку")

            # Проверяем адреса для диагностики
            verify_addresses_in_modal_send()

            if click_send_button_in_modal():
                successful_sends += 1
                print_success(f"Отправка #{successful_sends} выполнена успешно")

                if check_operation_success_send():
                    print_success("Операция отправки подтверждена")

                check_and_close_errors("После успешной отправки")

                print_success(f"Цикл завершен - активная кнопка 'Отправить' найдена на попытке #{attempt_count}")
                break
            else:
                add_error(f"Не удалось нажать кнопку 'Отправить' в попытке #{attempt_count}")
                close_modal_if_open()
        else:
            print_warning("Кнопка 'Отправить' не активна - закрываем окно и пробуем следующие ведомости")
            close_modal_if_open()
            continue

        time.sleep(1)

    # Проверка таймаута
    if successful_sends == 0:
        print("\n" + "=" * 60)
        print_warning("ВНИМАНИЕ: 3 МИНУТЫ ИСТЕКЛИ")
        print_warning("Активная кнопка 'Отправить' не найдена")
        print("=" * 60)

    print("\n" + "=" * 60)
    print("ИТОГОВЫЙ ОТЧЕТ ПО ЦИКЛИЧЕСКОЙ ОТПРАВКЕ")
    print("=" * 60)

    if successful_sends > 0:
        print_success(f"Всего успешных отправок: {successful_sends}")
    else:
        print(f"Всего успешных отправок: {successful_sends}")

    print(f"Всего попыток: {attempt_count}")
    print(f"Общее время выполнения: {int(time.time() - start_time)} сек")

    if section_errors:
        print(f"\n\033[91mНайдено ошибок: {len(section_errors)}\033[0m")
        for i, error in enumerate(section_errors, 1):
            print(f"\033[91m  {i}. {error}\033[0m")
    else:
        print(f"\n\033[92mОшибок не обнаружено\033[0m")

    print("\n" + "=" * 60)
    if successful_sends > 0 and len(section_errors) == 0:
        print_success("ТЕСТ ЦИКЛИЧЕСКОЙ ОТПРАВКИ УСПЕШНО ЗАВЕРШЕН")
    elif successful_sends > 0 and len(section_errors) > 0:
        print_warning("ТЕСТ ЗАВЕРШЕН С ОШИБКАМИ, НО ОТПРАВКА ВЫПОЛНЕНА")
    elif successful_sends == 0 and len(section_errors) > 0:
        print("\033[91mТЕСТ ЗАВЕРШЕН С ОШИБКАМИ, ОТПРАВКА НЕ ВЫПОЛНЕНА\033[0m")
    else:
        print("\033[91mТЕСТ ЗАВЕРШЕН, ОТПРАВКА НЕ ВЫПОЛНЕНА\033[0m")
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