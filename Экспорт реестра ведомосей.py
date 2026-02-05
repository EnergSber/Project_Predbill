from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import os
import pandas as pd
import glob
import re



# Определяем папку для загрузки
DOWNLOAD_FOLDER = r"C:\Экспорт_реестр_ведомостей_ПБ"

# Создаем папку если не существует
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)
    print(f"Создана папка для загрузки: {DOWNLOAD_FOLDER}")

# Очищаем папку от старых файлов
if os.path.exists(DOWNLOAD_FOLDER):
    print(f"Очистка папки: {DOWNLOAD_FOLDER}")
    for file in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, file)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                print(f"Удален старый файл: {file}")
            except:
                pass

# Настройки Chrome для обхода блокировки скачивания
chrome_options = Options()

# Критически важные настройки для скачивания
prefs = {
    "download.default_directory": DOWNLOAD_FOLDER,
    "download.prompt_for_download": False,  # Не спрашивать куда сохранять
    "download.directory_upgrade": True,
    "safebrowsing.enabled": False,  # ОТКЛЮЧИТЬ безопасный просмотр
    "safebrowsing.disable_download_protection": True,  # Разрешить загрузки
    "profile.default_content_setting_values.automatic_downloads": 1,
    "profile.content_settings.exceptions.automatic_downloads.*.setting": 1,

    # Отключаем блокировку опасных файлов
    "profile.default_content_setting_values.popups": 0,  # Разрешить popups
    "profile.default_content_setting_values.notifications": 2,

    # Разрешаем все типы загрузок
    "download.extensions_to_open": "",
    "download_restrictions": 0,

    # Отключаем предупреждения
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False,
}

chrome_options.add_experimental_option("prefs", prefs)

# Основные аргументы для обхода блокировки
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")  # Важно для обхода ограничений
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Скрыть автоматизацию

# КЛЮЧЕВЫЕ НАСТРОЙКИ ДЛЯ ОБХОДА БЛОКИРОВКИ СКАЧИВАНИЯ
chrome_options.add_argument("--allow-running-insecure-content")
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--ignore-ssl-errors")
chrome_options.add_argument("--unsafely-treat-insecure-origin-as-secure=http://10.5.121.74")
chrome_options.add_argument("--unsafely-treat-insecure-origin-as-secure=http://localhost")
chrome_options.add_argument("--unsafely-treat-insecure-origin-as-secure=http://127.0.0.1")

chrome_options.add_experimental_option("excludeSwitches",
                                       ["enable-automation"])  # Скрыть сообщение "Управляется автоматическим ПО"
chrome_options.add_experimental_option('useAutomationExtension', False)

# ========== ИНИЦИАЛИЗАЦИЯ ДРАЙВЕРА ==========

# Создаем драйвер с настройками
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Добавляем скрипт для скрытия автоматизации
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

driver.maximize_window()
wait = WebDriverWait(driver, 60)

# Данные для авторизации
URL = 'http://10.5.121.74/login'
USERNAME = 'predbill'
PASSWORD = 'predbill'

# Хранение ошибок
section_errors = []

print("=" * 60)
print("ТЕСТ РАЗДЕЛА: Экспорт ведомостей в Excel")
print("=" * 60)





# Функция для ожидания загрузки файла
def wait_for_file_download(filename_pattern="Реестр*ведомостей*.xlsx", timeout=60):
    """
    Ожидает появления файла в папке загрузки
    Возвращает путь к файлу или None
    """
    print(f"Ожидание загрузки файла по шаблону: {filename_pattern}")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Ищем файлы в целевой папке
            files = glob.glob(os.path.join(DOWNLOAD_FOLDER, filename_pattern))

            if files:
                # Берем самый новый файл
                latest_file = max(files, key=os.path.getctime)

                # Проверяем, что файл полностью загрузился (не частичный)
                file_size = os.path.getsize(latest_file)
                time.sleep(1)  # Даем время для завершения записи

                if file_size > 0:
                    print(f"Файл найден: {os.path.basename(latest_file)}")
                    print(f"Размер: {file_size} байт")
                    return latest_file

        except Exception as e:
            print(f"Ошибка при проверке файлов: {e}")

        time.sleep(2)
        print(f"Ожидание файла... прошло {int(time.time() - start_time)} секунд")

    print(f"Таймаут ожидания файла ({timeout} секунд)")
    return None


# Функция для добавления ошибок
def add_error(error_text):
    if error_text not in section_errors:
        section_errors.append(error_text)
        print(f"ОШИБКА: {error_text}")


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
            print(f"Выполнено: {action_name} (через родительский элемент)")
            time.sleep(0.5)
            return True
        except:
            actions = ActionChains(driver)
            actions.move_to_element(svg_element).click().perform()
            print(f"Выполнено: {action_name} (непосредственно на SVG)")
            time.sleep(0.5)
            return True

    except Exception as e:
        print(f"Не удалось {action_name}: {e}")
        return False


# Основной код теста

# 0. ОЧИСТКА ПАПКИ ЗАГРУЗКИ
print("\n" + "=" * 50)
print("ШАГ 0: ОЧИСТКА ПАПКИ ЗАГРУЗКИ")
print("=" * 50)



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
    print("Авторизация успешна")

except Exception as e:
    print(f"Авторизация не удалась: {e}")
    driver.quit()
    exit()

# 2. ПЕРЕХОД В РАЗДЕЛ "РЕЕСТР ВЕДОМОСТЕЙ"
print("\n" + "=" * 50)
print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ РЕЕСТР ВЕДОМОСТЕЙ")
print("=" * 50)

section_url = 'http://10.5.121.74/commercialControl/billingStatements'
section_name = 'Реестр ведомостей'

try:
    driver.get(section_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print(f"Переход в раздел '{section_name}'")
    time.sleep(3)

except Exception as e:
    add_error(f"Не удалось перейти в раздел: {e}")
    driver.quit()
    exit()

# 3. ПРОВЕРКА ОШИБОК НА СТРАНИЦЕ
print("\n" + "=" * 50)
print("ШАГ 3: ПРОВЕРКА ОШИБОК НА СТРАНИЦЕ")
print("=" * 50)

error_found = False
error_selectors = [
    "div.ant-notification-notice-error",
    "div.ant-alert-error",
    ".ant-message-error"
]

for selector in error_selectors:
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for elem in elements:
            try:
                if elem.is_displayed():
                    error_text = elem.text.strip()
                    if error_text:
                        add_error(f"Найдена ошибка: {error_text}")
                        error_found = True
            except:
                continue
    except:
        continue

if not error_found:
    print("Явных ошибок не найдено")

# 4. ВЫБОР ВСЕХ ВЕДОМОСТЕЙ ЧЕРЕЗ ЧЕКБОКС
print("\n" + "=" * 50)
print("ШАГ 4: ВЫБОР ВСЕХ ВЕДОМОСТЕЙ ЧЕРЕЗ ЧЕКБОКС")
print("=" * 50)

checkbox_selector = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__header > div > div > div:nth-child(1) > label"

try:
    checkbox = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, checkbox_selector))
    )

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
    time.sleep(0.5)

    checkbox.click()
    print("Выбраны все ведомости через чекбокс")
    time.sleep(2)

except Exception as e:
    add_error(f"Не удалось выбрать все ведомости: {e}")

# 5. ОТКРЫТИЕ КНОПКИ "ДЕЙСТВИЕ"
print("\n" + "=" * 50)
print("ШАГ 5: ОТКРЫТИЕ КНОПКИ 'ДЕЙСТВИЕ'")
print("=" * 50)

action_button_selector = "#root > section > section > div > div.ant-space.ant-space-horizontal.ant-space-align-center > div > div > div > div > div > button > div > div:nth-child(1) > span > svg"

if click_svg_element(action_button_selector, "Открыть меню 'Действие'"):
    print("Меню 'Действие' открыто")
    time.sleep(1)
else:
    add_error("Не удалось открыть меню 'Действие'")

# 6. ВЫБОР "ЭКСПОРТ"
print("\n" + "=" * 50)
print("ШАГ 6: ВЫБОР 'ЭКСПОРТ'")
print("=" * 50)

export_selector = "html > div > div > div > ul > li:nth-child(2) > span > button"

try:
    export_button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, export_selector))
    )

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", export_button)
    time.sleep(0.5)

    button_text = export_button.text.strip()
    print(f"Текст кнопки экспорта: '{button_text}'")

    export_button.click()
    print(f"Выбран пункт '{button_text}'")
    time.sleep(3)

except Exception as e:
    add_error(f"Не удалось выбрать 'Экспорт': {e}")

# 7. ПЕРЕХОД НА ВКЛАДКУ "ЭКСПОРТ РЕЕСТРА"
print("\n" + "=" * 50)
print("ШАГ 7: ПЕРЕХОД НА ВКЛАДКУ 'ЭКСПОРТ РЕЕСТРА'")
print("=" * 50)

tab_selector = "#tabView-tab-report"

try:
    tab_element = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, tab_selector))
    )

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab_element)
    time.sleep(0.5)

    tab_element.click()
    print("Перешли на вкладку 'Экспорт реестра'")
    time.sleep(1)

except Exception as e:
    add_error(f"Не удалось перейти на вкладку 'Экспорт реестра': {e}")

# 8. ВЫБОР ФОРМАТА XLS
print("\n" + "=" * 50)
print("ШАГ 8: ВЫБОР ФОРМАТА XLS")
print("=" * 50)

# Сначала ждем появления элементов
time.sleep(1)

try:
    # Ищем элемент с текстом XLS в модальном окне
    xls_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'xlsXLS', 'XLSXLS'), 'XLS')]")

    for element in xls_elements:
        try:
            element_text = element.text.strip()
            if "XLS" in element_text.upper() and len(element_text) < 10:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)
                element.click()
                print(f"Выбран формат: {element_text}")
                break
        except:
            continue

except Exception as e:
    print(f"Ошибка при выборе формата XLS: {e}")

# 9. ВЫБОР "ВЫДЕЛЕННЫЕ"
print("\n" + "=" * 50)
print("ШАГ 9: ВЫБОР 'ВЫДЕЛЕННЫЕ'")
print("=" * 50)

try:
    # Ищем элемент с текстом "Выделенные"
    selected_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Выделенные')]")

    for element in selected_elements:
        try:
            element_text = element.text.strip()
            if "Выделенные" in element_text:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)

                # Проверяем, не выбран ли уже
                element_class = element.get_attribute("class")
                if "ant-radio-button-checked" not in element_class:
                    element.click()
                    print("Выбраны 'Выделенные'")
                else:
                    print("'Выделенные' уже выбраны")
                break
        except:
            continue

except Exception as e:
    print(f"Ошибка при выборе 'Выделенные': {e}")

# 10. ЗАПОМИНАНИЕ КОЛИЧЕСТВА ВЕДОМОСТЕЙ
print("\n" + "=" * 50)
print("ШАГ 10: ЗАПОМИНАНИЕ КОЛИЧЕСТВА ВЕДОМОСТЕЙ")
print("=" * 50)

statements_count = 0

try:
    # Ищем div с классом counterTextModal
    counter_element = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.counterTextModal"))
    )

    counter_text = counter_element.text.strip()
    print(f"Текст счетчика: '{counter_text}'")

    # Извлекаем число
    numbers = re.findall(r'\d+', counter_text)
    if numbers:
        statements_count = int(numbers[0])
        print(f"Количество ведомостей для экспорта: {statements_count}")
    else:
        add_error("Не удалось извлечь число из текста счетчика")

except Exception as e:
    add_error(f"Не удалось найти счетчик ведомостей: {e}")

# 11. НАЖАТИЕ КНОПКИ "ВЫГРУЗИТЬ"
print("\n" + "=" * 50)
print("ШАГ 11: НАЖАТИЕ КНОПКИ 'ВЫГРУЗИТЬ'")
print("=" * 50)

try:
    # Ищем кнопку с текстом "Выгрузить"
    download_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Выгрузить')]"))
    )

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_button)
    time.sleep(0.5)

    button_text = download_button.text.strip()
    print(f"Нажимаем кнопку: '{button_text}'")

    download_button.click()
    print("Кнопка 'Выгрузить' нажата")
    time.sleep(3)  # Даем время на начало загрузки

except Exception as e:
    add_error(f"Не удалось нажать кнопку 'Выгрузить': {e}")

# 12. ОЖИДАНИЕ И ПОИСК ФАЙЛА
print("\n" + "=" * 50)
print("ШАГ 12: ОЖИДАНИЕ И ПОИСК ФАЙЛА")
print("=" * 50)

# Ожидаем загрузку файла
latest_file = wait_for_file_download("Реестр*ведомостей*.xlsx", timeout=30)

if not latest_file:
    # Пробуем другие шаблоны
    latest_file = wait_for_file_download("Реестр*.xlsx", timeout=20)

if not latest_file:
    # Пробуем поиск любого xlsx файла
    latest_file = wait_for_file_download("*.xlsx", timeout=15)

if latest_file:
    print(f"Файл успешно загружен: {os.path.basename(latest_file)}")
else:
    add_error("Файл не был загружен в указанную папку")

# 13. ПРОВЕРКА СОДЕРЖИМОГО ФАЙЛА
print("\n" + "=" * 50)
print("ШАГ 13: ПРОВЕРКА СОДЕРЖИМОГО ФАЙЛА")
print("=" * 50)

excel_rows_count = 0

if latest_file and statements_count > 0:
    try:
        print(f"Чтение файла: {os.path.basename(latest_file)}")

        # Устанавливаем openpyxl как движок для чтения Excel
        try:
            df = pd.read_excel(latest_file, engine='openpyxl')
            excel_rows_count = len(df)
            print(f"Количество строк в файле (с заголовком): {excel_rows_count}")

            if excel_rows_count > 0:
                print(f"Количество строк данных (без заголовка): {excel_rows_count - 1}")

                # Сравниваем
                if (excel_rows_count - 1) == statements_count:
                    print(f"СОВПАДЕНИЕ: В файле {excel_rows_count - 1} строк, ожидалось {statements_count}")
                else:
                    add_error(f"НЕСОВПАДЕНИЕ: В файле {excel_rows_count - 1} строк, а ожидалось {statements_count}")
            else:
                add_error("Файл пуст или содержит только заголовок")

        except Exception as e:
            print(f"Ошибка при чтении Excel с openpyxl: {e}")
            add_error(f"Не удалось прочитать Excel файл: {e}")

    except Exception as e:
        add_error(f"Ошибка при обработке файла: {e}")
else:
    if statements_count == 0:
        add_error("Не удалось получить количество ведомостей для сравнения")

# 14. ФИНАЛЬНЫЙ ОТЧЕТ
print("\n" + "=" * 60)
print("ИТОГОВЫЙ ОТЧЕТ")
print("=" * 60)

print(f"\nРаздел: {section_name}")
print(f"URL: {section_url}")

print(f"\nРезультаты проверки экспорта:")
print(f"  Количество ведомостей для экспорта: {statements_count}")
print(f"  Файл экспорта: {os.path.basename(latest_file) if latest_file else 'Не найден'}")
print(f"  Строк в файле (без заголовка): {excel_rows_count - 1 if excel_rows_count > 0 else 0}")

print(f"\nИтог проверки экспорта:")

if not section_errors:
    if latest_file and statements_count > 0 and (excel_rows_count - 1) == statements_count:
        print("\033[92m" + "РЕЗУЛЬТАТ: ТЕСТ УСПЕШНО ЗАВЕРШЕН" + "\033[0m")
        print("\033[92m" + "Все этапы выполнены успешно!" + "\033[0m")
        print("\033[92m" + "Количество ведомостей в файле совпадает с ожидаемым" + "\033[0m")
    else:
        print("РЕЗУЛЬТАТ: ТЕСТ ЗАВЕРШЕН С ПРЕДУПРЕЖДЕНИЯМИ")
        print("Проверьте логи для деталей")
else:
    print("РЕЗУЛЬТАТ: ТЕСТ ПРОВАЛЕН")
    print(f"\nНайдено ошибок: {len(section_errors)}")
    print("Список ошибок:")
    for i, error in enumerate(section_errors, 1):
        print(f"  {i}. {error}")

print(f"\n" + "=" * 60)

# 15. ЗАКРЫТИЕ БРАУЗЕРА
try:
    print("Закрытие браузера...")
    time.sleep(2)
    driver.quit()
    print("Браузер успешно закрыт")
except Exception as e:
    print(f"Не удалось закрыть браузера: {e}")