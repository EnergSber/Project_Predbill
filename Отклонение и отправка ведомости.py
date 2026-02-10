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

        # Ищем таблицу
        table_selector = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body"
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

        print("Нашли контейнер поля причины")

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

    # 12. НАЖАТИЕ "СОХРАНИТЬ"
    print("\n" + "=" * 50)
    print("ШАГ 12: НАЖАТИЕ КНОПКИ 'СОХРАНИТЬ'")
    print("=" * 50)

    if not click_save_button():
        add_error("Не удалось нажать кнопку 'Сохранить'")

    # 13. ФИНАЛЬНАЯ ПРОВЕРКА
    print("\n" + "=" * 50)
    print("ШАГ 13: ФИНАЛЬНАЯ ПРОВЕРКА")
    print("=" * 50)

    print("Ожидание завершения операции...")
    time.sleep(3)

    # Проверяем ошибки финально
    check_and_close_errors("Финальная проверка")

    # 14. ИТОГОВЫЙ ОТЧЕТ
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
    # Закрытие браузера
    try:
        print("\nЗакрытие браузера...")
        driver.quit()
        print("Браузер успешно закрыт")
    except Exception as e:
        print(f"Не удалось закрыть браузер: {e}")