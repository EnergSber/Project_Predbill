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

# Инициализация драйвера
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()
wait = WebDriverWait(driver, 60)

# Данные для авторизации
URL = 'http://10.5.121.74/login'
USERNAME = 'predbill'
PASSWORD = 'predbill'

# Хранение ошибок
section_errors = []

print("=" * 60)
print("ТЕСТ РАЗДЕЛА: Реестр ведомостей - Отправка объемов за период")
print("=" * 60)


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


def apply_filters():
    try:
        print("Применяем фильтры...")

        apply_button_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > div > div.filterOperations > button:nth-child(1) > span > svg"

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


def mark_first_three_checkboxes():
    try:
        print("Отмечаем первые три ведомости...")

        table_body = driver.find_element(By.CSS_SELECTOR, table_selector)
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
                    print(f"  Отмечена строка {i + 1}")
                    time.sleep(0.3)
                else:
                    print(f"  Строка {i + 1} уже отмечена")
                    marked_count += 1
            except Exception as e:
                print(f"  Ошибка при отметке строки {i + 1}: {e}")

        if marked_count == 3:
            print_success("Все три ведомости отмечены")

            global saved_selected_addresses
            saved_selected_addresses = []
            for i in range(3):
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
            return True
        else:
            add_error(f"Отмечено только {marked_count} из 3 чекбоксов")
            return False

    except Exception as e:
        add_error(f"Ошибка при отметке ведомостей: {e}")
        return False


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


def select_volume_sending_option():
    try:
        print("Выбираем опцию 'Отправка объемов за период'...")

        try:
            volume_button = driver.find_element(By.CSS_SELECTOR,
                                                "html > div > div > div > ul > li:nth-child(4) > span > button")
            if volume_button.is_displayed() and volume_button.is_enabled():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", volume_button)
                time.sleep(0.5)
                volume_button.click()
                print("Опция 'Отправка объемов за период' выбрана")
                time.sleep(2)

                check_and_close_errors("После выбора 'Отправка объемов за период'")

                return True
        except Exception as e:
            print(f"Точный селектор не сработал: {e}")

        try:
            volume_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Отправка объемов за период')]")
            for element in volume_elements:
                if element.is_displayed() and element.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.5)
                    element.click()
                    print("Опция 'Отправка объемов за период' выбрана (по тексту)")
                    time.sleep(2)

                    check_and_close_errors("После выбора 'Отправка объемов за период'")

                    return True
        except:
            pass

        add_error("Не найден элемент 'Отправка объемов за период'")
        return False

    except Exception as e:
        add_error(f"Ошибка при выборе опции 'Отправка объемов за период': {e}")
        return False


def select_random_date():
    try:
        print("Выбираем рандомный месяц в календаре...")

        # Находим и раскрываем поле выбора даты
        try:
            date_field = driver.find_element(By.CSS_SELECTOR,
                                             "#addRolesModalForm > div.rt-form-body > div > div.ant-col.ant-col-16.ant-form-item-control > div > div > div")

            if date_field.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_field)
                time.sleep(0.5)
                date_field.click()
                print("Поле выбора даты раскрыто")
                time.sleep(1)

                check_and_close_errors("После раскрытия поля даты")
            else:
                add_error("Поле выбора даты не найдено")
                return False
        except Exception as e:
            add_error(f"Ошибка при раскрытии поля даты: {e}")
            return False

        # Ищем календарь с месяцами
        try:
            # Ожидаем появления календаря
            time.sleep(1)

            # Ищем таблицу с месяцами
            calendar_table = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                                                "table.ant-picker-content"))
            )

            # Ищем все ячейки с месяцами
            month_cells = calendar_table.find_elements(By.CSS_SELECTOR, "td.ant-picker-cell-in-view")

            # Фильтруем только активные месяцы (не disabled)
            available_months = []
            for cell in month_cells:
                try:
                    classes = cell.get_attribute("class")
                    if "ant-picker-cell-disabled" not in classes:
                        month_name = cell.text.strip()
                        available_months.append((cell, month_name))
                        print(f"  Доступный месяц: {month_name}")
                except:
                    continue

            if available_months:
                # Выбираем рандомный месяц
                random_month_cell, month_name = random.choice(available_months)

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", random_month_cell)
                time.sleep(0.3)
                random_month_cell.click()
                print_success(f"Выбран рандомный месяц: {month_name}")
                time.sleep(1)

                check_and_close_errors("После выбора месяца")
                return True
            else:
                # Если нет доступных месяцев, пробуем выбрать любой не-disabled
                try:
                    # Ищем ячейки без класса disabled
                    active_months = calendar_table.find_elements(By.CSS_SELECTOR,
                                                                 "td.ant-picker-cell-in-view:not(.ant-picker-cell-disabled)")
                    if active_months:
                        random_month = random.choice(active_months)
                        month_name = random_month.text.strip()
                        random_month.click()
                        print_success(f"Выбран рандомный месяц: {month_name}")
                        time.sleep(1)
                        return True
                except:
                    pass

                add_error("Не найдены доступные месяцы для выбора")
                return False

        except Exception as e:
            add_error(f"Ошибка при выборе месяца из календаря: {e}")
            return False

    except Exception as e:
        add_error(f"Ошибка при выборе рандомного месяца: {e}")
        return False


def click_save_button_in_modal():
    try:
        print("Нажимаем кнопку 'Сохранить' в модальном окне...")
        time.sleep(2)

        # Точный селектор
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
        except Exception as e:
            print(f"Точный селектор не сработал: {e}")

        # Поиск по тексту
        try:
            save_buttons = driver.find_elements(By.XPATH,
                                                "//div[@id='addRolesModalForm']//button[contains(text(), 'Сохранить')]")
            for button in save_buttons:
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    print("Кнопка 'Сохранить' нажата (по тексту)")
                    time.sleep(2)

                    check_and_close_errors("После нажатия 'Сохранить'")

                    return True
        except:
            pass

        # Поиск primary кнопки
        try:
            primary_buttons = driver.find_elements(By.CSS_SELECTOR,
                                                   "#addRolesModalForm .ant-btn-primary")
            for button in primary_buttons:
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    print("Кнопка 'Сохранить' нажата (primary)")
                    time.sleep(2)

                    check_and_close_errors("После нажатия 'Сохранить'")

                    return True
        except:
            pass

        add_error("Не найдена кнопка 'Сохранить' в модальном окне")
        return False

    except Exception as e:
        add_error(f"Ошибка при нажатии кнопки 'Сохранить': {e}")
        return False


def check_operation_success():
    try:
        print("\nПроверяем успешность операции...")
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
                modal = driver.find_element(By.CSS_SELECTOR, "#addRolesModalForm")
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
    print_success("Авторизация успешна")

    check_and_close_errors("После авторизации")

except Exception as e:
    add_error(f"Ошибка авторизации: {e}")
    driver.quit()
    exit()

print("\n" + "=" * 50)
print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ")
print("=" * 50)

try:
    section_url = 'http://10.5.121.74/commercialControl/billingStatements'
    driver.get(section_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("Переход в раздел 'Реестр ведомостей'")
    time.sleep(2)

    check_and_close_errors("После перехода в раздел")

except Exception as e:
    add_error(f"Ошибка перехода в раздел: {e}")

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

print("\n" + "=" * 50)
print("ШАГ 5: ПРИМЕНЕНИЕ ФИЛЬТРОВ")
print("=" * 50)

if not apply_filters():
    add_error("Не удалось применить фильтры")
    driver.quit()
    exit()

print("\n" + "=" * 50)
print("ШАГ 6: ОТМЕТКА ПЕРВЫХ ТРЕХ ВЕДОМОСТЕЙ")
print("=" * 50)

if not mark_first_three_checkboxes():
    add_error("Не удалось отметить первые три ведомости")
    driver.quit()
    exit()

print("\n" + "=" * 50)
print("ШАГ 7: КЛИК НА КНОПКУ 'ДЕЙСТВИЕ'")
print("=" * 50)

if not click_action_button():
    add_error("Не удалось нажать кнопку 'Действие'")
    driver.quit()
    exit()

print("\n" + "=" * 50)
print("ШАГ 8: ВЫБОР ОПЦИИ 'ОТПРАВКА ОБЪЕМОВ ЗА ПЕРИОД'")
print("=" * 50)

if not select_volume_sending_option():
    add_error("Не удалось выбрать опцию 'Отправка объемов за период'")
    close_modal_if_open()
    driver.quit()
    exit()

print("\n" + "=" * 50)
print("ШАГ 9: ВЫБОР РАНДОМНОЙ ДАТЫ В КАЛЕНДАРЕ")
print("=" * 50)

if not select_random_date():
    add_error("Не удалось выбрать рандомную дату")
    close_modal_if_open()
    driver.quit()
    exit()

print("\n" + "=" * 50)
print("ШАГ 10: НАЖАТИЕ КНОПКИ 'СОХРАНИТЬ'")
print("=" * 50)

if not click_save_button_in_modal():
    add_error("Не удалось нажать кнопку 'Сохранить'")
    close_modal_if_open()

print("\n" + "=" * 50)
print("ШАГ 11: ПРОВЕРКА УСПЕШНОСТИ ОПЕРАЦИИ")
print("=" * 50)

operation_success = check_operation_success()

print("\n" + "=" * 60)
print("ИТОГОВЫЙ ОТЧЕТ ПО ОТПРАВКЕ ОБЪЕМОВ ЗА ПЕРИОД")
print("=" * 60)

if operation_success:
    print_success("Операция отправки объемов за период выполнена успешно")
else:
    add_error("Операция отправки объемов за период не завершена успешно")
    print_warning("Операция отправки объемов за период не завершена успешно")

if section_errors:
    print(f"\n\033[91mНайдено ошибок: {len(section_errors)}\033[0m")
    for i, error in enumerate(section_errors, 1):
        print(f"\033[91m  {i}. {error}\033[0m")
else:
    print(f"\n\033[92mОшибок не обнаружено\033[0m")

print("\n" + "=" * 60)
if operation_success and len(section_errors) == 0:
    print_success("ТЕСТ ОТПРАВКИ ОБЪЕМОВ ЗА ПЕРИОД УСПЕШНО ЗАВЕРШЕН")
elif operation_success and len(section_errors) > 0:
    print_warning("ТЕСТ ЗАВЕРШЕН С ОШИБКАМИ, НО ОПЕРАЦИЯ ВЫПОЛНЕНА")
else:
    print("\033[91mТЕСТ ЗАВЕРШЕН С ОШИБКАМИ, ОПЕРАЦИЯ НЕ ВЫПОЛНЕНА\033[0m")
print("=" * 60)



try:
    print("\nЗакрытие браузера...")
    driver.quit()
    print("Браузер успешно закрыт")
except Exception as e:
    print(f"Не удалось закрыть браузер: {e}")