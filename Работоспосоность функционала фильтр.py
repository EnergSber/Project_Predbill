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
APPLY_SELECTOR = "button[type='submit']"
TABLE_SELECTOR = "#root > section > section > main > form > div > div > div > div:nth-child(1) > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body"

# Хранение ошибок
section_errors = []

print("=" * 60)
print("ТЕСТ РАЗДЕЛА: Реестр ведомостей")
print("=" * 60)


# Функция для добавления ошибок
def add_error(error_text):
    if error_text not in section_errors:
        section_errors.append(error_text)
        print(f"⚠ {error_text}")


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
                            print(f"  ✓ Закрыта всплывающая ошибка")
                            time.sleep(0.2)
                            return True
                    except:
                        continue
            except:
                continue
        return False
    except Exception as e:
        print(f"  ⚠ Ошибка при закрытии ошибок: {e}")
        return False


# Функция для ожидания загрузки
def wait_for_page_load():
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
            print(f"✓ {action_name} (через родительский элемент)")
            time.sleep(0.5)
            return True
        except:
            actions = ActionChains(driver)
            actions.move_to_element(svg_element).click().perform()
            print(f"✓ {action_name} (непосредственно на SVG)")
            time.sleep(0.5)
            return True

    except Exception as e:
        print(f"✗ Не удалось {action_name}: {e}")
        return False


# Функция для обработки выпадающего списка с рандомным выбором значения
def process_select_random_value(field_selector, field_name):
    """
    Открывает выпадающий список и выбирает случайное доступное значение (кроме "Выбрать все")
    """
    try:
        print(f"\n🎯 Обрабатываем поле: {field_name}")

        # Находим поле
        field_element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, field_selector))
        )

        # Прокручиваем к полю
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field_element)
        time.sleep(0.5)

        # Кликаем чтобы открыть список
        print(f"  📋 Открываем выпадающий список...")
        field_element.click()
        time.sleep(1)

        # Ждем появления выпадающего списка
        dropdown_selector = ".ant-select-dropdown:not(.ant-select-dropdown-hidden)"
        try:
            dropdown = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, dropdown_selector))
            )
            print(f"  ✓ Выпадающий список открылся")
        except:
            print(f"  ⚠ Не видим выпадающий список")
            return False

        # Ищем все элементы в списке
        try:
            all_options = dropdown.find_elements(By.CSS_SELECTOR, ".ant-select-item-option")
            print(f"  🔍 Найдено опций в списке: {len(all_options)}")

            if not all_options:
                print(f"  ⚠ Список пуст")
                # Закрываем список
                field_element.click()
                return False

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
                print(f"  ⚠ Нет подходящих значений (только 'Выбрать все')")
                # Закрываем список
                field_element.click()
                return False

            # Выбираем случайное значение
            random_option, random_text = random.choice(valid_options)
            print(f"  🎲 Выбираем случайное значение: '{random_text}'")

            # Прокручиваем к выбранному элементу
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", random_option)
            time.sleep(0.3)

            # Кликаем на элемент
            random_option.click()
            print(f"  ✅ Выбрали случайное значение: '{random_text}'")
            time.sleep(0.5)
            return True

        except Exception as e:
            print(f"  ❌ Ошибка при работе со списком: {e}")
            return False

    except Exception as e:
        print(f"❌ Ошибка при обработке поля '{field_name}': {e}")
        add_error(f"Ошибка в поле '{field_name}': {e}")
        return False


# Функция для обработки выпадающего списка с выбором "Выбрать все"
def process_select_all_field(field_selector, field_name):
    """
    Открывает выпадающий список и выбирает "Выбрать все"
    """
    try:
        print(f"\n🎯 Обрабатываем поле: {field_name}")

        # Находим поле
        field_element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, field_selector))
        )

        # Прокручиваем к полю
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field_element)
        time.sleep(0.5)

        # Кликаем чтобы открыть список
        print(f"  📋 Открываем выпадающий список...")
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
            print(f"  ✅ Выбрали 'Выбрать все'")
            time.sleep(0.5)
            return True
        else:
            print(f"  ⚠ Не нашли 'Выбрать все'")
            return False

    except Exception as e:
        print(f"❌ Ошибка при обработке поля '{field_name}': {e}")
        add_error(f"Ошибка в поле '{field_name}': {e}")
        return False


# Функция для обработки поля "Параллельные ПУ" (рандомный выбор)
def process_parallel_pu_field():
    """
    Обрабатывает поле "Параллельные ПУ" - выбирает случайное значение
    """
    try:
        print(f"\n🎯 Обрабатываем поле: Параллельные ПУ")

        # Селектор поля
        field_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(18) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div"

        # Используем общую функцию для рандомного выбора
        return process_select_random_value(field_selector, "Параллельные ПУ")

    except Exception as e:
        print(f"❌ Ошибка при обработке поля 'Параллельные ПУ': {e}")
        add_error(f"Ошибка в поле 'Параллельные ПУ': {e}")
        return False


# Функция для обработки текстового поля "Номер ПУ"
def process_pu_number_field():
    """
    Обрабатывает текстовое поле "Номер ПУ" - вводит значение 158
    """
    try:
        print(f"\n🎯 Обрабатываем поле: Номер ПУ")

        # Ищем поле по ID или классу
        field_selectors = [
            "input#meteringDeviceSeries",
            "input[placeholder='Введите значение']",
            ".ant-input[type='text']"
        ]

        field_element = None
        for selector in field_selectors:
            try:
                field_element = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"  ✅ Нашли поле по селектору: {selector}")
                break
            except:
                continue

        if not field_element:
            print(f"  ❌ Не нашли поле Номер ПУ")
            return False

        # Прокручиваем к полю
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field_element)
        time.sleep(0.5)

        # Вводим значение
        value = "158"
        print(f"  ⌨️  Вводим значение: {value}")

        field_element.click()
        time.sleep(0.3)
        field_element.clear()
        time.sleep(0.3)
        field_element.send_keys(value)

        print(f"  ✅ Значение введено")
        return True

    except Exception as e:
        print(f"❌ Ошибка при обработке поля 'Номер ПУ': {e}")
        add_error(f"Ошибка в поле 'Номер ПУ': {e}")
        return False


# Функция для обработки поля адреса (как раньше, без рандом)
def process_address_field():
    """
    Обрабатывает сложное поле адреса (как в оригинальном коде, без случайного выбора)
    """
    try:
        print(f"\n🎯 Обрабатываем поле: Адрес")

        # Селекторы для поля адреса
        address_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(10) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div"
        address_input_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(10) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div.searchableSelectPopup > div.searchableSelectPopupInsider > div.searchBox.Адрес > input"
        address_list_selector = "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(10) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div.searchableSelectPopup > div.searchableSelectPopupInsider > div.searchBox.Адрес > ul"
        address_value = "1-й Амбулаторный пр., д.2/6"

        print(f"  🔍 Ищем поле адреса...")

        # 1. Находим и кликаем на поле адреса
        try:
            address_field = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, address_selector))
            )

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", address_field)
            time.sleep(0.5)

            print(f"  📍 Кликаем на поле адреса...")
            address_field.click()
            time.sleep(1.5)

        except Exception as e:
            print(f"  ❌ Не удалось найти/кликнуть на поле адреса: {e}")
            return False

        # 2. Находим поле ввода
        try:
            address_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, address_input_selector))
            )
            print(f"  ✅ Нашли поле ввода адреса")
        except:
            print(f"  ❌ Не удалось найти поле ввода адреса")
            return False

        # 3. Вводим адрес
        print(f"  ⌨️  Вводим адрес: {address_value}")
        try:
            address_input.clear()
            time.sleep(0.3)
            address_input.send_keys(address_value)
            print(f"  ✓ Адрес введен")
            time.sleep(3)  # Ждем загрузки результатов

        except Exception as e:
            print(f"  ❌ Ошибка при вводе адреса: {e}")
            return False

        # 4. Ищем и выбираем адрес из списка (как раньше - выбираем первый)
        print(f"  🔍 Ищем список адресов...")
        try:
            address_list = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, address_list_selector))
            )
            print(f"  ✅ Список адресов найден")

            address_items = address_list.find_elements(By.TAG_NAME, "li")
            print(f"  📊 Найдено адресов: {len(address_items)}")

            if address_items:
                # Выбираем ПЕРВЫЙ адрес (как было в оригинальном коде)
                first_item = address_items[0]
                first_item_text = first_item.text.strip()
                first_item.click()
                print(f"  ✅ Выбрали адрес из списка: '{first_item_text}'")
                time.sleep(0.5)
                return True
            else:
                print(f"  ⚠ Список адресов пуст")
                return False

        except Exception as e:
            print(f"  ❌ Ошибка при работе со списком адресов: {e}")
            return False

    except Exception as e:
        print(f"❌ Общая ошибка при обработке поля 'Адрес': {e}")
        add_error(f"Ошибка в поле 'Адрес': {e}")
        return False


# Функция для нажатия Tab
def press_tab():
    """Нажимает клавишу Tab"""
    try:
        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB).perform()
        print(f"  ↩ Нажали Tab")
        time.sleep(0.3)
        return True
    except:
        return False


# Функция для применения фильтров
def apply_filters():
    try:
        print("\n🎯 Применяем фильтры...")
        time.sleep(1)

        try_methods = [
            lambda: driver.find_element(By.CSS_SELECTOR, "button[type='submit']"),
            lambda: driver.find_element(By.CSS_SELECTOR, "button.ant-btn-primary"),
            lambda: driver.find_element(By.XPATH, "//button[contains(text(), 'Применить')]"),
            lambda: driver.find_element(By.XPATH, "//button[contains(text(), 'Поиск')]"),
            lambda: driver.find_element(By.XPATH, "//span[contains(text(), 'Применить')]/parent::button"),
        ]

        for i, method in enumerate(try_methods, 1):
            try:
                button = method()
                if button.is_displayed() and button.is_enabled():
                    print(f"  ✅ Нашли кнопку (метод {i})")

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    time.sleep(0.3)

                    actions = ActionChains(driver)
                    actions.move_to_element(button).click().perform()
                    print(f"  ✓ Применили фильтры")
                    time.sleep(1)
                    return True
            except:
                continue

        print("⚠ Не удалось найти активную кнопку 'Применить'")
        return False

    except Exception as e:
        print(f"✗ Ошибка при применении фильтров: {e}")
        add_error(f"Ошибка при применении фильтров: {e}")
        return False


# ОСНОВНОЙ КОД

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

except Exception as e:
    print(f"✗ Авторизация не удалась: {e}")
    driver.quit()
    exit()

# 2. ПЕРЕХОД В РАЗДЕЛ
print("\n" + "=" * 50)
print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ")
print("=" * 50)

section_url = 'http://10.5.121.74/commercialControl/billingStatements'
section_name = 'Реестр ведомостей'

try:
    driver.get(section_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print(f"✓ Переход в раздел '{section_name}'")
    time.sleep(2)

except Exception as e:
    add_error(f"Не удалось перейти в раздел: {e}")
    driver.quit()
    exit()

# 3. ПРОВЕРКА ОШИБОК
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
    print("✓ Явных ошибок не найдено")

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
    print("✓ Фильтр открыт")

time.sleep(2)

# 5. СБРОС ФИЛЬТРОВ
print("\n" + "=" * 50)
print("ШАГ 5: СБРОС ФИЛЬТРОВ")
print("=" * 50)

reset_clicked = False

for attempt in range(max_attempts):
    if click_svg_element(RESET_SELECTOR, f"Сбросить фильтры (попытка {attempt + 1})"):
        reset_clicked = True
        break
    else:
        time.sleep(0.5)

if not reset_clicked:
    add_error("Не удалось сбросить фильтры")
else:
    print("✓ Фильтры сброшены")

# 6. ОЖИДАНИЕ ЗАГРУЗКИ ПОСЛЕ СБРОСА
print("\n" + "=" * 50)
print("ШАГ 6: ОЖИДАНИЕ ЗАГРУЗКИ ДАННЫХ")
print("=" * 50)

load_duration = wait_for_page_load()

# 7. ЗАПОЛНЕНИЕ ПОЛЕЙ ФИЛЬТРА (в правильном порядке)
print("\n" + "=" * 50)
print("ШАГ 7: ЗАПОЛНЕНИЕ ПОЛЕЙ ФИЛЬТРА")
print("=" * 50)

# Определяем селекторы полей (в порядке заполнения)
field_configs = [
    # Первые два поля - выбираем "Выбрать все"
    {"name": "Категория",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(2) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div > div.ant-select-selection-overflow",
     "type": "select_all"},
    {"name": "Статус ведомости",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(3) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div",
     "type": "select_all"},

    # Остальные поля - выбираем случайное доступное значение (кроме "Выбрать все")
    {"name": "Причина",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(4) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div",
     "type": "select_random"},
    {"name": "Дополнительное поле",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(5) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div > div",
     "type": "select_random"},
    {"name": "Тепловой пункт",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(6) > div.ant-col.ant-col-14.ant-form-item-control > div > div > span > input",
     "type": "input", "value": "04-06-0601/032"},

    # Новые поля (по порядку из вашего описания)
    {"name": "АО",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(8) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div > div.ant-select-selection-overflow",
     "type": "select_random"},
    {"name": "Район",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(9) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div > div.ant-select-selection-overflow",
     "type": "select_random"},

    # Поле Адрес (как раньше, без рандом)
    {"name": "Адрес", "type": "address"},

    # Параллельные ПУ (рандомный выбор)
    {"name": "Параллельные ПУ", "type": "parallel_pu"},

    # Филиал (случайное значение)
    {"name": "Филиал",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(11) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div",
     "type": "select_random"},

    # Предприятие (случайное значение)
    {"name": "Предприятие",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(12) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div",
     "type": "select_random"},

    # Тип объекта (случайное значение)
    {"name": "Тип объекта",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(13) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div",
     "type": "select_random"},

    # Номер ПУ (текстовое поле)
    {"name": "Номер ПУ", "type": "pu_number"},

    # Тип точки учета (случайное значение)
    {"name": "Тип точки учета",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(17) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div",
     "type": "select_random"},

    # Марка ПУ (случайное значение)
    {"name": "Марка ПУ",
     "selector": "body > div:nth-child(3) > div > div.ant-drawer-content-wrapper > div > div > div > form > div > div:nth-child(16) > div.ant-col.ant-col-14.ant-form-item-control > div > div > div > div",
     "type": "select_random"},
]

# Обрабатываем поля в правильном порядке
results = {}
for i, config in enumerate(field_configs, 1):
    field_name = config["name"]
    field_type = config.get("type", "select_random")

    print(f"\n[{i}/{len(field_configs)}] Поле: {field_name}")

    success = False

    if field_type == "select_all":
        # Выбираем "Выбрать все"
        success = process_select_all_field(config["selector"], field_name)

    elif field_type == "select_random":
        # Выбираем случайное доступное значение (кроме "Выбрать все")
        success = process_select_random_value(config["selector"], field_name)

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
            print(f"  ✅ Ввели: {config['value']}")
            success = True
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            success = False

    elif field_type == "address":
        # Особое поле адреса (как раньше, без рандом)
        success = process_address_field()

    elif field_type == "parallel_pu":
        # Поле "Параллельные ПУ" (рандомный выбор)
        success = process_parallel_pu_field()

    elif field_type == "pu_number":
        # Поле "Номер ПУ"
        success = process_pu_number_field()

    results[field_name] = success

    # Нажимаем Tab после каждого поля (кроме последнего)
    if i < len(field_configs):
        press_tab()
        time.sleep(0.5)

print("\n✓ Все поля обработаны")

# 8. ПРИМЕНЕНИЕ ФИЛЬТРОВ
print("\n" + "=" * 50)
print("ШАГ 8: ПРИМЕНЕНИЕ ФИЛЬТРОВ")
print("=" * 50)

filters_applied = apply_filters()

# 9. ОЖИДАНИЕ ЗАГРУЗКИ
print("\n" + "=" * 50)
print("ШАГ 9: ОЖИДАНИЕ ЗАГРУЗКИ ДАННЫХ")
print("=" * 50)

if filters_applied:
    load_duration_after_filter = wait_for_page_load()
    print(f"✓ Данные загружены после применения фильтров: {load_duration_after_filter:.1f} сек")
else:
    print("⚠ Фильтры не были применены")

# 10. СБРОС ФИЛЬТРОВ В КОНЦЕ
print("\n" + "=" * 50)
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
    add_error("Не удалось сбросить фильтры в конце")
else:
    print("✓ Фильтры сброшены (финальный сброс)")

# 11. ОЖИДАНИЕ ЗАГРУЗКИ ПОСЛЕ СБРОСА
print("\n" + "=" * 50)
print("ШАГ 11: ОЖИДАНИЕ ЗАГРУЗКИ ДАННЫХ ПОСЛЕ СБРОСА")
print("=" * 50)

load_duration_after_reset = wait_for_page_load()

# 12. ФИНАЛЬНЫЙ ОТЧЕТ
print("\n" + "=" * 60)
print("ИТОГОВЫЙ ОТЧЕТ")
print("=" * 60)

print(f"\n📊 Раздел: {section_name}")
print(f"📎 URL: {section_url}")
print(f"⏱️  Время загрузки после сброса: {load_duration:.1f} сек")
if filters_applied:
    print(f"⏱️  Время загрузки после фильтров: {load_duration_after_filter:.1f} сек")
print(f"⏱️  Время загрузки после финального сброса: {load_duration_after_reset:.1f} сек")

print(f"\n📋 Результаты обработки полей:")
for config in field_configs:
    field_name = config["name"]
    status = results.get(field_name, False)
    print(f"  {'✓' if status else '✗'} {field_name}")
print(f"  {'✓' if filters_applied else '✗'} Фильтры применены")
print(f"  {'✓' if reset_clicked_final else '✗'} Финальный сброс фильтров")

if section_errors:
    print(f"\n❌ Найдено ошибок: {len(section_errors)}")
    print("\nСписок ошибок:")
    for i, error in enumerate(section_errors, 1):
        print(f"  {i}. {error}")
else:
    print(f"\n✅ Все шаги выполнены успешно!")
    print("✅ Раздел работает корректно")

print(f"\n{'=' * 60}")

# Закрытие браузера
try:
    print("\nНажмите Enter для закрытия браузера...")
    input()
    print("Закрытие браузера...")
    driver.quit()
    print("✓ Браузер успешно закрыт")
except Exception as e:
    print(f"⚠ Не удалось закрыть браузера: {e}")