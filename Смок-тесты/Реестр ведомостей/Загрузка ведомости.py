import os
import time
import sys
import re
import xml.etree.ElementTree as ET
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

current_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Директория проекта: {current_dir}")

TARGET_FILENAME = "06-01-0610_004.html"
FILE_PATH = os.path.join(current_dir, TARGET_FILENAME)

# ============================================================================
# ЧТЕНИЕ ДАННЫХ ИЗ HTML ФАЙЛА (ИЗВЛЕЧЕНИЕ XML ИЗ SCRIPT ТЕГА)
# ============================================================================
print("\n" + "=" * 60)
print("ЧТЕНИЕ ДАННЫХ ИЗ ФАЙЛА ВЕДОМОСТИ")
print("=" * 60)

file_data = {
    'address': '',
    'system': '',  # Тип точки (SYSTEM)
    'model': '',
    'serial': ''
}

try:
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Извлекаем содержимое между тегами <AV_PROTOCOL> и </AV_PROTOCOL>
    pattern = r'<AV_PROTOCOL>(.*?)</AV_PROTOCOL>'
    match = re.search(pattern, content, re.DOTALL)

    if match is not None:
        xml_content = match.group(1)
        print("Найден AV_PROTOCOL в файле")

        # Парсим XML
        try:
            # Добавляем корневой элемент для парсинга
            root = ET.fromstring(f"<root>{xml_content}</root>")

            # Ищем AV_HEADER
            av_header = root.find('.//AV_HEADER')
            if av_header is None:
                av_header = root.find('.//av_header')

            if av_header is not None:
                # 1. Адрес
                address = av_header.find('.//ADDRESS')
                if address is None:
                    address = av_header.find('.//address')
                if address is not None and address.text is not None:
                    file_data['address'] = address.text.strip()
                    print(f"Адрес из файла: {file_data['address']}")

                # 2. Тип точки (SYSTEM)
                system = av_header.find('.//SYSTEM')
                if system is None:
                    system = av_header.find('.//system')
                if system is not None and system.text is not None:
                    file_data['system'] = system.text.strip()
                    print(f"Тип точки (SYSTEM) из файла: {file_data['system']}")

                # 3. Модель ПУ
                model = av_header.find('.//MODEL')
                if model is None:
                    model = av_header.find('.//model')
                if model is not None and model.text is not None:
                    file_data['model'] = model.text.strip()
                    print(f"Модель ПУ из файла: {file_data['model']}")

                # 4. Номер ПУ (серийный номер)
                serial = av_header.find('.//SERIAL')
                if serial is None:
                    serial = av_header.find('.//serial')
                if serial is not None and serial.text is not None:
                    file_data['serial'] = serial.text.strip()
                    print(f"Номер ПУ из файла: {file_data['serial']}")
            else:
                print("AV_HEADER не найден в XML")

        except ET.ParseError as e:
            print(f"Ошибка парсинга XML: {e}")
    else:
        print("AV_PROTOCOL не найден в файле")

        # Альтернативный поиск: ищем отдельные теги
        print("Пробую альтернативный метод поиска...")

        # Ищем ADDRESS
        addr_match = re.search(r'<ADDRESS>(.*?)</ADDRESS>', content, re.IGNORECASE)
        if addr_match is not None:
            file_data['address'] = addr_match.group(1).strip()
            print(f"Адрес из файла (альт): {file_data['address']}")

        # Ищем SYSTEM
        system_match = re.search(r'<SYSTEM>(.*?)</SYSTEM>', content, re.IGNORECASE)
        if system_match is not None:
            file_data['system'] = system_match.group(1).strip()
            print(f"Тип точки (SYSTEM) из файла (альт): {file_data['system']}")

        # Ищем MODEL
        model_match = re.search(r'<MODEL>(.*?)</MODEL>', content, re.IGNORECASE)
        if model_match is not None:
            file_data['model'] = model_match.group(1).strip()
            print(f"Модель ПУ из файла (альт): {file_data['model']}")

        # Ищем SERIAL
        serial_match = re.search(r'<SERIAL>(.*?)</SERIAL>', content, re.IGNORECASE)
        if serial_match is not None:
            file_data['serial'] = serial_match.group(1).strip()
            print(f"Номер ПУ из файла (альт): {file_data['serial']}")

except Exception as e:
    print(f"Ошибка при чтении файла: {e}")

# Проверяем, удалось ли прочитать данные
if not any(file_data.values()):
    print("\nНЕ УДАЛОСЬ ПРОЧИТАТЬ ДАННЫЕ ИЗ ФАЙЛА!")
    print("Использую тестовые данные для отладки...")
    file_data = {
        'address': 'Синявинская ул., д.11, корп.3',
        'system': 'ТЭ',
        'model': 'SA-94',
        'serial': 'Тест123'
    }
    print(f"Тестовые данные: {file_data}")

if not os.path.exists(FILE_PATH):
    print(f"Создаю файл: {TARGET_FILENAME}")
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.write("""<HTML>
<HEAD>
<meta http-equiv="X-UA-Compatible" content="IE=EmulateIE9"/>
<meta http-equiv="content-type" content="text/html; charset=UTF-8" />
<TITLE></TITLE>
<script id='AVProtocol' type='application/xml'>
<AV_PROTOCOL>
    <AV_HEADER>
        <ADDRESS>Синявинская ул., д.11, корп.3</ADDRESS>
        <SYSTEM>ТЭ</SYSTEM>
        <MODEL>SA-94</MODEL>
        <SERIAL>Тест123</SERIAL>
    </AV_HEADER>
</AV_PROTOCOL>
</script>
</HEAD>
<BODY>
</BODY>
</HTML>""")

print(f"\nФайл для загрузки: {FILE_PATH}")
print(f"Размер: {os.path.getsize(FILE_PATH)} байт")
print(f"Данные из файла: {file_data}")

# ============================================================================
# НАСТРОЙКА CHROME
# ============================================================================
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False
})

chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')

try:
    from webdriver_manager.chrome import ChromeDriverManager

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("Chrome запущен успешно")
except Exception as e:
    print(f"Ошибка запуска Chrome: {e}")
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("Chrome запущен без менеджера драйверов")
    except Exception as e2:
        print(f"Не удалось запустить Chrome: {e2}")
        sys.exit()

driver.maximize_window()
wait = WebDriverWait(driver, 20)

# Данные для авторизации
from config import USERNAME, PASSWORD
URL = 'http://10.5.121.74/login'

print("\n" + "=" * 60)
print("1. АВТОРИЗАЦИЯ В СИСТЕМЕ")
print("=" * 60)

try:
    driver.get(URL)
    time.sleep(2)

    username_field = wait.until(EC.presence_of_element_located((By.ID, "normal_login_username")))
    username_field.send_keys(USERNAME)
    print("Логин введен")

    password_field = driver.find_element(By.ID, "normal_login_password")
    password_field.send_keys(PASSWORD)
    print("Пароль введен")

    login_button = driver.find_element(By.CSS_SELECTOR, '.ant-btn.ant-btn-primary.w-100.mb-s')
    login_button.click()
    print("Кнопка входа нажата")

    wait.until_not(EC.url_contains('login'))
    print("Авторизация успешна")
    time.sleep(2)

except Exception as e:
    print(f"Ошибка авторизации: {e}")
    driver.quit()
    sys.exit()

print("\n" + "=" * 60)
print("2. ПЕРЕХОД В РЕЕСТР ВЕДОМОСТЕЙ")
print("=" * 60)

try:
    driver.get('http://10.5.121.74/commercialControl/billingStatements')
    time.sleep(3)
    print("Раздел открыт")
except Exception as e:
    print(f"Ошибка перехода: {e}")
    driver.quit()
    sys.exit()

print("\n" + "=" * 60)
print("3. ПОИСК СКРЫТОГО ПОЛЯ ДЛЯ ЗАГРУЗКИ ФАЙЛА")
print("=" * 60)

try:
    file_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')

    if len(file_inputs) > 0:
        print(f"Найдено {len(file_inputs)} полей для загрузки файла")
        file_input = file_inputs[0]

        driver.execute_script("arguments[0].style.display = 'block';", file_input)
        driver.execute_script("arguments[0].style.visibility = 'visible';", file_input)
        driver.execute_script("arguments[0].style.opacity = '1';", file_input)

        time.sleep(1)

        print(f"Отправляю файл напрямую: {FILE_PATH}")
        file_input.send_keys(FILE_PATH)

        print("Файл загружен напрямую через input!")
        time.sleep(2)
        skip_to_upload = True
    else:
        print("Поля input[type='file'] не найдены")
        skip_to_upload = False

except Exception as e:
    print(f"Ошибка при прямой загрузке: {e}")
    skip_to_upload = False

if not skip_to_upload:
    print("\n" + "=" * 60)
    print("4. ОТКРЫТИЕ МЕНЮ 'ДЕЙСТВИЕ' (стандартный путь)")
    print("=" * 60)

    try:
        action_button = None

        try:
            action_button = driver.find_element(By.XPATH, "//button[contains(., 'Действие')]")
        except:
            try:
                action_button = driver.find_element(By.CSS_SELECTOR, "button.ant-dropdown-trigger")
            except:
                action_button = driver.execute_script("""
                    var buttons = document.querySelectorAll('button');
                    for (var btn of buttons) {
                        if (btn.textContent and btn.textContent.includes('Действие')) {
                            return btn;
                        }
                    }
                    return null;
                """)

        if action_button is not None:
            action_button.click()
            print("Меню 'Действие' открыто")
            time.sleep(1)
        else:
            raise Exception("Кнопка 'Действие' не найдена")

    except Exception as e:
        print(f"Не удалось открыть меню: {e}")
        driver.quit()
        sys.exit()

    print("\n" + "=" * 60)
    print("5. НАЖАТИЕ НА 'ЗАГРУЗКА' В МЕНЮ")
    print("=" * 60)

    try:
        upload_button = None
        time.sleep(1)

        try:
            upload_button = driver.find_element(By.XPATH, "//li//button[contains(., 'Загрузка')]")
        except:
            try:
                upload_button = driver.find_element(By.XPATH, "//button[.//*[contains(@class, 'cloud-upload')]]")
            except:
                upload_button = driver.execute_script("""
                    var menu = document.querySelector('.ant-dropdown-menu, [role="menu"]');
                    if (!menu) return null;
                    var buttons = menu.querySelectorAll('button');
                    for (var btn of buttons) {
                        if (btn.textContent and btn.textContent.includes('Загрузка')) {
                            return btn;
                        }
                    }
                    return null;
                """)

        if upload_button is not None:
            upload_button.click()
            print("Кнопка 'Загрузка' нажата")
            time.sleep(2)

            try:
                modal_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
                if len(modal_inputs) > 0:
                    print(f"Найдено {len(modal_inputs)} полей в модальном окне")
                    modal_inputs[0].send_keys(FILE_PATH)
                    print("Файл загружен через модальное окно")
                    skip_to_upload = True
                else:
                    print("В модальном окне нет поля для загрузки")
            except:
                print("Не удалось найти поле в модальном окне")
        else:
            raise Exception("Кнопка 'Загрузка' не найдена")

    except Exception as e:
        print(f"Не удалось нажать 'Загрузка': {e}")
        driver.quit()
        sys.exit()

print("\n" + "=" * 60)
print("6. ПОИСК И НАЖАТИЕ КНОПКИ 'ЗАГРУЗИТЬ'")
print("=" * 60)

print("Жду появление формы загрузки...")
time.sleep(3)

try:
    submit_button = None

    for attempt in range(5):
        print(f"Попытка {attempt + 1} найти кнопку 'Загрузить'...")

        try:
            modal_buttons = driver.find_elements(By.CSS_SELECTOR, '.ant-modal button')
            for btn in modal_buttons:
                if "Загрузить" in btn.text:
                    submit_button = btn
                    print("Кнопка найдена в модальном окне")
                    break
        except:
            pass

        if submit_button is None:
            try:
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in all_buttons:
                    btn_text = btn.text.strip()
                    if btn_text == "Загрузить":
                        submit_button = btn
                        print("Кнопка найдена среди всех кнопок")
                        break
            except:
                pass

        if submit_button is not None:
            break

        time.sleep(1)

    if submit_button is not None:
        submit_button.click()
        print("Кнопка 'Загрузить' нажата")

        print("\n" + "=" * 50)
        print("ЗАКРЫВАЮ ОКНО WINDOWS ПОСЛЕ НАЖАТИЯ 'ЗАГРУЗИТЬ'")
        print("=" * 50)

        time.sleep(2)

        try:
            import pyautogui

            print("Нажимаю ESC для закрытия окна Windows...")
            pyautogui.press('esc')
            time.sleep(1)
            pyautogui.press('esc')
            print("Окно Windows закрыто по ESC")
        except Exception as e:
            print(f"Не удалось закрыть окно Windows через pyautogui: {e}")
            try:
                import ctypes

                VK_ESCAPE = 0x1B
                ctypes.windll.user32.keybd_event(VK_ESCAPE, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_ESCAPE, 0, 2, 0)
                print("Окно Windows закрыто через Windows API")
            except:
                print("Не удалось закрыть окно Windows")

        # УМНОЕ ОЖИДАНИЕ: Ждем пока пропадет индикатор загрузки
        print("\nОжидание завершения загрузки...")
        try:
            WebDriverWait(driver, 30).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, 'svg[data-icon="loading"]'))
            )
            print("Индикатор загрузки исчез - загрузка завершена")
        except Exception as e:
            print(f"Индикатор загрузки не найден или не исчез: {e}")
            time.sleep(5)

    else:
        print("Кнопка 'Загрузить' не найдена")

except Exception as e:
    print(f"Ошибка при работе с кнопкой: {e}")

print("\n" + "=" * 60)
print("7. НАЖАТИЕ КНОПКИ 'ПЕРЕЙТИ В ЖУРНАЛ'")
print("=" * 60)

print("Поиск кнопки 'Перейти в журнал'...")

try:
    journal_button = None

    for attempt in range(10):
        print(f"Попытка {attempt + 1} найти кнопку 'Перейти в журнал'...")

        try:
            buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Перейти в журнал')]")
            if len(buttons) > 0:
                for btn in buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        journal_button = btn
                        print("Кнопка 'Перейти в журнал' найдена по тексту")
                        break
        except:
            pass

        if journal_button is None:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, "button.ant-btn.ant-btn-primary.ml-s")
                for btn in buttons:
                    if btn.is_displayed() and "Перейти в журнал" in btn.text:
                        journal_button = btn
                        print("Кнопка найдена по классу ant-btn-primary")
                        break
            except:
                pass

        if journal_button is None:
            try:
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in all_buttons:
                    btn_text = btn.text.strip()
                    if btn_text == "Перейти в журнал":
                        journal_button = btn
                        print("Кнопка найдена среди всех кнопок")
                        break
            except:
                pass

        if journal_button is not None:
            break

        time.sleep(1)

    if journal_button is not None:
        print(f"Найдена кнопка с текстом: '{journal_button.text}'")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", journal_button)
        time.sleep(0.5)

        try:
            journal_button.click()
            print("Кнопка 'Перейти в журнал' нажата")
        except:
            driver.execute_script("arguments[0].click();", journal_button)
            print("Кнопка 'Перейти в журнал' нажата через JavaScript")

        print("Ожидание перехода в журнал...")
        time.sleep(3)
        print("Успешный переход в журнал!")
    else:
        print("Кнопка 'Перейти в журнал' не найдена")

except Exception as e:
    print(f"Ошибка при поиске кнопки 'Перейти в журнал': {e}")

print("\n" + "=" * 60)
print("8. ПРОВЕРКА ДАННЫХ В ЖУРНАЛЕ")
print("=" * 60)

print("Ожидание загрузки данных в журнале...")
time.sleep(5)

# Флаг для отслеживания успешности теста
test_passed = True
test_failures = []
mismatches = []

# Список прочерков для проверки
empty_indicators = ["", "-", "—", "–", "−", "---", "--", "––", " ", "  ", "   "]

# Данные из журнала
journal_data = {
    'address': '',
    'system': '',  # Тип точки (SYSTEM)
    'model': '',
    'serial': '',
    'status': ''  # Статус загрузки
}

try:
    # Ждем загрузки таблицы
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.BaseTable__table'))
    )

    print("\n" + "=" * 60)
    print("СРАВНЕНИЕ ДАННЫХ ИЗ ФАЙЛА И ИЗ ЖУРНАЛА")
    print("=" * 60)

    print(f"\nДанные из файла ведомости:")
    print(f"  Адрес:      '{file_data['address']}'")
    print(f"  Тип точки:  '{file_data['system']}'")
    print(f"  Модель ПУ:  '{file_data['model']}'")
    print(f"  Номер ПУ:   '{file_data['serial']}'")

    # ==========================================
    # 1. Проверка АДРЕСА
    # ==========================================
    print("\n1. Проверка адреса:")
    try:
        address_selectors = [
            '#root > section > section > main > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body > div > div > div:nth-child(3)',
            '.BaseTable__row > div:nth-child(3)',
            'div[role="gridcell"]:nth-child(3)'
        ]

        for selector in address_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if len(elements) > 0 and elements[0].text.strip():
                journal_data['address'] = elements[0].text.strip()
                print(f"  Адрес в журнале: '{journal_data['address']}'")
                break

        if journal_data['address']:
            if journal_data['address'] not in empty_indicators:
                if journal_data['address'] == file_data['address']:
                    print("  ✓ Адрес СОВПАДАЕТ с данными из файла")
                else:
                    error_msg = f"  ✗ Адрес НЕ СОВПАДАЕТ: файл='{file_data['address']}', журнал='{journal_data['address']}'"
                    print(error_msg)
                    test_passed = False
                    mismatches.append(f"Адрес: '{file_data['address']}' != '{journal_data['address']}'")
            else:
                error_msg = f"  ✗ Адрес пустой или содержит прочерк: '{journal_data['address']}'"
                print(error_msg)
                test_passed = False
                test_failures.append("Адрес в журнале пустой или содержит прочерк")
        else:
            error_msg = "  ✗ Адрес не найден в журнале"
            print(error_msg)
            test_passed = False
            test_failures.append("Адрес не найден в журнале")

    except Exception as e:
        error_msg = f"  ✗ Ошибка при проверке адреса: {e}"
        print(error_msg)
        test_passed = False
        test_failures.append(f"Ошибка проверки адреса")

    # ==========================================
    # 2. Проверка ТИПА ТОЧКИ (SYSTEM)
    # ==========================================
    print("\n2. Проверка типа точки (SYSTEM):")
    try:
        system_selectors = [
            '#root > section > section > main > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body > div > div > div:nth-child(4)',
            '.BaseTable__row > div:nth-child(4)',
            'div[role="gridcell"]:nth-child(4)'
        ]

        for selector in system_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if len(elements) > 0 and elements[0].text.strip():
                journal_data['system'] = elements[0].text.strip()
                print(f"  Тип точки в журнале: '{journal_data['system']}'")
                break

        if journal_data['system']:
            if journal_data['system'] not in empty_indicators:
                if journal_data['system'] == file_data['system']:
                    print("  ✓ Тип точки СОВПАДАЕТ с данными из файла")
                else:
                    error_msg = f"  ✗ Тип точки НЕ СОВПАДАЕТ: файл='{file_data['system']}', журнал='{journal_data['system']}'"
                    print(error_msg)
                    test_passed = False
                    mismatches.append(f"Тип точки: '{file_data['system']}' != '{journal_data['system']}'")
            else:
                error_msg = f"  ✗ Тип точки пустой или содержит прочерк: '{journal_data['system']}'"
                print(error_msg)
                test_passed = False
                test_failures.append("Тип точки в журнале пустой или содержит прочерк")
        else:
            error_msg = "  ✗ Тип точки не найден в журнале"
            print(error_msg)
            test_passed = False
            test_failures.append("Тип точки не найден в журнале")

    except Exception as e:
        error_msg = f"  ✗ Ошибка при проверке типа точки: {e}"
        print(error_msg)
        test_passed = False
        test_failures.append(f"Ошибка проверки типа точки")

    # ==========================================
    # 3. Проверка МОДЕЛИ ПУ
    # ==========================================
    print("\n3. Проверка модели ПУ:")
    try:
        model_selectors = [
            '#root > section > section > main > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body > div > div > div:nth-child(5) > span',
            '.BaseTable__row > div:nth-child(5) span',
            'div[role="gridcell"]:nth-child(5) span'
        ]

        for selector in model_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if len(elements) > 0 and elements[0].text.strip():
                journal_data['model'] = elements[0].text.strip()
                print(f"  Модель ПУ в журнале: '{journal_data['model']}'")
                break

        if journal_data['model']:
            if journal_data['model'] not in empty_indicators:
                if journal_data['model'] == file_data['model']:
                    print("  ✓ Модель ПУ СОВПАДАЕТ с данными из файла")
                else:
                    error_msg = f"  ✗ Модель ПУ НЕ СОВПАДАЕТ: файл='{file_data['model']}', журнал='{journal_data['model']}'"
                    print(error_msg)
                    test_passed = False
                    mismatches.append(f"Модель ПУ: '{file_data['model']}' != '{journal_data['model']}'")
            else:
                error_msg = f"  ✗ Модель ПУ пустая или содержит прочерк: '{journal_data['model']}'"
                print(error_msg)
                test_passed = False
                test_failures.append("Модель ПУ в журнале пустая или содержит прочерк")
        else:
            error_msg = "  ✗ Модель ПУ не найдена в журнале"
            print(error_msg)
            test_passed = False
            test_failures.append("Модель ПУ не найдена в журнале")

    except Exception as e:
        error_msg = f"  ✗ Ошибка при проверке модели ПУ: {e}"
        print(error_msg)
        test_passed = False
        test_failures.append(f"Ошибка проверки модели ПУ")

    # ==========================================
    # 4. Проверка НОМЕРА ПУ (серийного номера)
    # ==========================================
    print("\n4. Проверка номера ПУ:")
    try:
        serial_selectors = [
            '#root > section > section > main > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body > div > div > div:nth-child(6) > span',
            '.BaseTable__row > div:nth-child(6) span',
            'div[role="gridcell"]:nth-child(6) span'
        ]

        for selector in serial_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if len(elements) > 0 and elements[0].text.strip():
                journal_data['serial'] = elements[0].text.strip()
                print(f"  Номер ПУ в журнале: '{journal_data['serial']}'")
                break

        if journal_data['serial']:
            if journal_data['serial'] not in empty_indicators:
                if journal_data['serial'] == file_data['serial']:
                    print("  ✓ Номер ПУ СОВПАДАЕТ с данными из файла")
                else:
                    error_msg = f"  ✗ Номер ПУ НЕ СОВПАДАЕТ: файл='{file_data['serial']}', журнал='{journal_data['serial']}'"
                    print(error_msg)
                    test_passed = False
                    mismatches.append(f"Номер ПУ: '{file_data['serial']}' != '{journal_data['serial']}'")
            else:
                error_msg = f"  ✗ Номер ПУ пустой или содержит прочерк: '{journal_data['serial']}'"
                print(error_msg)
                test_passed = False
                test_failures.append("Номер ПУ в журнале пустой или содержит прочерк")
        else:
            error_msg = "  ✗ Номер ПУ не найден в журнале"
            print(error_msg)
            test_passed = False
            test_failures.append("Номер ПУ не найден в журнале")

    except Exception as e:
        error_msg = f"  ✗ Ошибка при проверке номера ПУ: {e}"
        print(error_msg)
        test_passed = False
        test_failures.append(f"Ошибка проверки номера ПУ")

    # ==========================================
    # 5. Проверка СТАТУСА ЗАГРУЗКИ (не пустой, может быть иконка)
    # ==========================================
    print("\n5. Проверка статуса загрузки:")
    try:
        # Сначала ищем иконку (крестик или галочку)
        status_icon_found = False
        icon_selectors = [
            '#root > section > section > main > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body > div > div > div.BaseTable__row-cell.BaseTable__row-cell--align-center > div > span > svg',
            '.BaseTable__row-cell--align-center svg',
            'svg[data-icon="close"]',  # красный крестик
            'svg[data-icon="check"]',  # зеленая галочка
            'svg[data-icon="check-circle"]',
            'svg[data-icon="close-circle"]'
        ]

        for selector in icon_selectors:
            icons = driver.find_elements(By.CSS_SELECTOR, selector)
            if len(icons) > 0:
                status_icon_found = True
                print(f"  ✓ Найдена иконка статуса (OK)")
                journal_data['status'] = "иконка присутствует"
                break

        # Если иконка не найдена, ищем текст
        if not status_icon_found:
            status_selectors = [
                '#root > section > section > main > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body > div > div > div.BaseTable__row-cell.BaseTable__row-cell--align-center > div',
                '.BaseTable__row-cell--align-center div',
                '[data-testid="status-column"]',
                'div[class*="status"]'
            ]

            for selector in status_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elements) > 0 and elements[0].text.strip():
                    journal_data['status'] = elements[0].text.strip()
                    print(f"  Статус загрузки в журнале: '{journal_data['status']}'")
                    break

        # Проверяем результат
        if status_icon_found or (journal_data['status'] and journal_data['status'] not in empty_indicators):
            print("  ✓ Статус загрузки заполнен (есть данные или иконка)")
        else:
            error_msg = "  ✗ Статус загрузки пустой или отсутствует"
            print(error_msg)
            test_passed = False
            test_failures.append("Статус загрузки пустой или отсутствует")

    except Exception as e:
        error_msg = f"  ✗ Ошибка при проверке статуса загрузки: {e}"
        print(error_msg)
        test_passed = False
        test_failures.append(f"Ошибка проверки статуса загрузки")

except Exception as e:
    print(f"Ошибка при проверке данных в журнале: {e}")
    test_passed = False
    test_failures.append(f"Общая ошибка проверки журнала: {e}")

print("\n" + "=" * 60)
print("9. ИТОГИ ТЕСТИРОВАНИЯ")
print("=" * 60)

if test_passed:
    print("\n✅ ТЕСТ ПРОЙДЕН УСПЕШНО!")
    print("   Все данные из файла совпадают с данными в журнале:")
    print(f"   - Адрес: {file_data['address']}")
    print(f"   - Тип точки: {file_data['system']}")
    print(f"   - Модель ПУ: {file_data['model']}")
    print(f"   - Номер ПУ: {file_data['serial']}")
    print(f"   - Статус загрузки: присутствует")
else:
    print("\n❌ ТЕСТ ПРОВАЛЕН!")

    if len(test_failures) > 0:
        print("\n   Ошибки:")
        for i, failure in enumerate(test_failures, 1):
            print(f"   {i}. {failure}")

    if len(mismatches) > 0:
        print("\n   Несовпадения данных:")
        for i, mismatch in enumerate(mismatches, 1):
            print(f"   {i}. {mismatch}")

    print("\n   ВНИМАНИЕ: Данные в журнале не соответствуют загруженному файлу!")

print("\n" + "=" * 60)
print("10. ЗАВЕРШЕНИЕ ТЕСТА")
print("=" * 60)

# Не закрываем браузер сразу, даем посмотреть результат
#input()
time.sleep(2)
driver.quit()
print("Chrome закрыт")

# Завершаем с соответствующим кодом выхода
if not test_passed:
    sys.exit(1)