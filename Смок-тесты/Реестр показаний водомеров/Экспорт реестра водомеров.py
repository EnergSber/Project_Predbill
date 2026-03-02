"""
ТЕСТ: Экспорт реестра показаний водомеров в Excel через веб-интерфейс
"""

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.firefox import GeckoDriverManager
import time
import os
import pandas as pd
import glob
import re
import random
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

print("=" * 60)
print("ТЕСТ РАЗДЕЛА: Экспорт реестра показаний водомеров в Excel")
print("=" * 60)

# Определяем папку для загрузки
DOWNLOAD_FOLDER = r"C:\Экспорт_реестр_водомеров"

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)
    print(f"Создана папка для загрузки: {DOWNLOAD_FOLDER}")

if os.path.exists(DOWNLOAD_FOLDER):
    print(f"Очистка папки: {DOWNLOAD_FOLDER}")
    for file in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, file)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                print(f"Удален: {file}")
            except:
                pass

# Настройки для Firefox
firefox_options = Options()

firefox_paths = [
    r"C:\Program Files\Mozilla Firefox\firefox.exe",
    r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
]

firefox_found = False
for path in firefox_paths:
    if os.path.exists(path):
        firefox_options.binary_location = path
        print(f"Найден Firefox: {path}")
        firefox_found = True
        break

if not firefox_found:
    print("Firefox не найден в стандартных путях!")
    exit()

# Настройки загрузки для Firefox
firefox_options.set_preference("browser.download.folderList", 2)
firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
firefox_options.set_preference("browser.download.dir", DOWNLOAD_FOLDER)
firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,"
                               "application/vnd.ms-excel,"
                               "application/excel,"
                               "application/x-excel,"
                               "application/x-msexcel,"
                               "application/octet-stream")
firefox_options.set_preference("pdfjs.disabled", True)

# ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ ДЛЯ СКРЫТИЯ ПАНЕЛИ ЗАГРУЗОК
firefox_options.set_preference("browser.download.alwaysOpenPanel", False)
firefox_options.set_preference("browser.download.panel.shown", False)
firefox_options.set_preference("browser.download.panel.suppress", True)
firefox_options.set_preference("browser.download.manager.alertOnEXEOpen", False)
firefox_options.set_preference("browser.download.manager.focusWhenStarting", False)
firefox_options.set_preference("browser.download.manager.useWindow", False)
firefox_options.set_preference("browser.download.manager.showAlertOnComplete", False)
firefox_options.set_preference("browser.download.manager.closeWhenDone", True)

# ИНИЦИАЛИЗАЦИЯ ДРАЙВЕРА
try:
    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=firefox_options)
    print("Firefox успешно запущен")
except Exception as e:
    print(f"Ошибка запуска Firefox: {e}")
    try:
        driver = webdriver.Firefox(options=firefox_options)
        print("Firefox запущен без менеджера драйверов")
    except Exception as e2:
        print(f"Не удалось запустить Firefox: {e2}")
        exit()

driver.maximize_window()
wait = WebDriverWait(driver, 30)

# Данные для авторизации
from config import USERNAME, PASSWORD
URL = 'http://10.5.121.74/login'

# Селекторы для раздела
SECTION_URL = 'http://10.5.121.74/commercialControl/watermeterStatements'
SECTION_NAME = 'Реестр показаний водомеров'

# Чекбокс выбора всех записей
CHECKBOX_ALL_SELECTOR = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__header > div > div > div:nth-child(1) > label > span > input"

# Кнопка "Действие"
ACTION_BUTTON_SELECTOR = "button.ant-btn-link.ant-dropdown-trigger.inlineButton"

# Пункт меню "Экспорт"
EXPORT_MENU_ITEM_SELECTOR = "html > div > div > div > ul > li:nth-child(2) > span > button"

# Радиокнопки выбора типа экспорта
EXPORT_BY_FILTER_SELECTOR = "#statusChoose > label:nth-child(1)"  # По фильтру
EXPORT_BY_SELECTED_SELECTOR = "#statusChoose > label:nth-child(2)"  # Выделенные

# Селекторы фильтра
FILTER_OPEN_SELECTOR = "svg[data-icon='filter']"

# ИСПРАВЛЕННЫЙ селектор кнопки сброса
FILTER_RESET_BUTTON_SELECTOR = "body > div:nth-child(4) > div > div.ant-drawer-content-wrapper > div > div > div > div.filterHeaderRow > div.filterOperations > button:nth-child(2)"

# ИСПРАВЛЕННЫЙ селектор кнопки применения фильтра
FILTER_APPLY_BUTTON_SELECTOR = "body > div:nth-child(4) > div > div.ant-drawer-content-wrapper > div > div > div > div.filterHeaderRow > div.filterOperations > button:nth-child(1)"

# ИСПРАВЛЕННЫЙ селектор для поля АО
AO_FIELD_SELECTOR = "input#aoCode"
AO_SELECTOR = "div.ant-select-selector"

AO_LABEL_SELECTOR = "label[for='aoCode']"  # label с for="aoCode"
AO_INPUT_SELECTOR = "input#aoCode"  # Инпут по ID
AO_CONTAINER_SELECTOR = "div.ant-select-selector"  # Контейнер для клика

FILTER_APPLY_BUTTON = "//button[contains(., 'Применить')]"

# Кнопка выгрузки
EXPORT_DOWNLOAD_BUTTON = "//button[contains(., 'Выгрузить')]"

# Счетчик записей в окне экспорта
COUNTER_MODAL_SELECTOR = "div.counterTextModal"

# ===========================================

section_errors = []
results_comparison = {}
selected_ao_value = None


def add_error_with_context(error_text, context):
    full_error = f"[{context}] {error_text}"
    if full_error not in section_errors:
        section_errors.append(full_error)
        print(f"ОШИБКА: {full_error}")
    return section_errors


def smart_wait_for_errors_disappear():
    print(f"Ожидание исчезновения ошибок...")
    start_wait_time = time.time()
    max_wait_time = 5

    def try_close_error():
        try:
            close_selectors = [
                "span.ant-notification-notice-close-x",
                ".ant-notification-notice-close",
                ".ant-alert-close-icon",
                ".ant-message-notice-close",
                "[aria-label='close']",
                ".anticon-close"
            ]
            for selector in close_selectors:
                try:
                    close_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in close_buttons:
                        try:
                            if btn.is_displayed() or btn.is_enabled():
                                try:
                                    btn.click()
                                except:
                                    driver.execute_script("arguments[0].click();", btn)
                                print(f"Найден и кликнут крестик")
                                time.sleep(0.2)
                                return True
                        except:
                            try:
                                driver.execute_script("arguments[0].click();", btn)
                                print(f"Кликнут крестик через JS")
                                time.sleep(0.2)
                                return True
                            except:
                                continue
                except:
                    continue
            return False
        except:
            return False

    def check_for_persistent_errors():
        error_check_selectors = [
            "div.ant-notification-notice-error",
            "div.ant-alert-error",
            ".ant-message-error",
        ]
        for selector in error_check_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    try:
                        if elem.is_displayed():
                            error_text = elem.text.strip()
                            if error_text and len(error_text) > 3:
                                text_lower = error_text.lower()
                                if ("не обнаружено" not in text_lower and
                                        "не найдено" not in text_lower and
                                        "успешно" not in text_lower and
                                        "успешн" not in text_lower and
                                        "завершено" not in text_lower and
                                        "completed" not in text_lower and
                                        "готово" not in text_lower):
                                    return True
                    except:
                        continue
            except:
                continue
        return False

    try:
        while time.time() - start_wait_time < max_wait_time:
            if check_for_persistent_errors():
                elapsed = time.time() - start_wait_time
                if elapsed > 0.5:
                    print(f"Ошибка держится {elapsed:.1f}с, пробуем закрыть...")
                    if try_close_error():
                        print(f"Попытка закрытия выполнена")
                        time.sleep(0.5)
                    else:
                        print(f"Не удалось найти кнопку закрытия")
                time.sleep(0.5)
            else:
                print(f"Ошибки исчезли")
                return True
        print(f"Ошибки не исчезли за {max_wait_time} секунд, продолжаем...")
        return False
    except Exception as e:
        print(f"Исключение в умном ожидании: {e}")
        return False


def wait_for_page_load(context=""):
    print(f"Ожидание загрузки данных [{context}]...")
    load_start = time.time()
    try:
        loading_selectors = [
            "div.ant-spin.ant-spin-spinning",
            "div.ant-spin-spinning",
            "div.ant-spin-text",
            "span.anticon-loading.anticon-spin",
            "span.ant-spin-dot",
            "div.ant-spin-container"
        ]
        for selector in loading_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        if element.is_displayed():
                            element_class = element.get_attribute("class") or ""
                            if ("ant-spin-spinning" in element_class or "anticon-spin" in element_class):
                                print(f"Найден спиннер загрузки, ожидаем...")
                                wait.until(EC.invisibility_of_element(element))
                                print(f"Спиннер исчез")
                    except:
                        continue
            except:
                continue
        load_duration = time.time() - load_start
        print(f"Загрузка данных завершена за {load_duration:.1f} секунд [{context}]")
        return load_duration
    except Exception as e:
        print(f"Ошибка при ожидании загрузки [{context}]: {e}")
        return time.time() - load_start


def wait_for_file_download(filename_pattern="*.xlsx", timeout=60):
    print(f"Ожидание загрузки файла по шаблону: {filename_pattern}")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            files = glob.glob(os.path.join(DOWNLOAD_FOLDER, filename_pattern))
            if files:
                latest_file = max(files, key=os.path.getctime)
                time.sleep(2)
                try:
                    file_size = os.path.getsize(latest_file)
                    if file_size > 1000:
                        with open(latest_file, 'rb') as f:
                            header = f.read(100)
                        if b'PK' in header[:2] or file_size > 1024:
                            print(f"Файл найден: {os.path.basename(latest_file)}")
                            print(f"Размер: {file_size:,} байт")
                            return latest_file
                except:
                    continue
        except:
            pass
        time.sleep(2)
        elapsed = int(time.time() - start_time)
        print(f"Ожидание файла... {elapsed}/{timeout} сек")
    print(f"Таймаут ожидания файла ({timeout} секунд)")
    return None


def read_excel_file_safe(file_path):
    try:
        file_size = os.path.getsize(file_path)
        if file_size < 100:
            return pd.DataFrame()
        engines = [
            ('openpyxl', 'openpyxl'),
            ('xlrd', 'xlrd'),
            ('odf', 'odf'),
            ('pyxlsb', 'pyxlsb'),
        ]
        file_ext = os.path.splitext(file_path)[1].lower()
        for engine_name, engine in engines:
            try:
                if file_ext == '.xlsx':
                    df = pd.read_excel(file_path, engine=engine, header=None)
                elif file_ext == '.xls':
                    df = pd.read_excel(file_path, engine=engine, header=None)
                else:
                    df = pd.read_excel(file_path, engine=engine, header=None)
                if df is not None:
                    return df
            except:
                continue
        return pd.DataFrame()
    except Exception as e:
        print(f"Ошибка чтения файла {file_path}: {e}")
        return pd.DataFrame()


def count_data_rows_in_excel(df):
    if df.empty:
        return 0
    HEADER_ROWS = 1
    if len(df) <= HEADER_ROWS:
        return 0
    data_rows = 0
    for idx in range(HEADER_ROWS, len(df)):
        row = df.iloc[idx]
        row_has_data = False
        for cell in row:
            if pd.notna(cell):
                cell_str = str(cell).strip()
                if cell_str and cell_str not in ['', 'nan', 'NaN', 'None']:
                    row_has_data = True
                    break
        if row_has_data:
            data_rows += 1
    print(f"Всего строк в файле: {len(df)}, строк заголовка: {HEADER_ROWS}, строк данных: {data_rows}")
    return data_rows


def click_svg_element(svg_selector, action_name, context=""):
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
            print(f"Выполнено: {action_name} [{context}]")
            time.sleep(0.5)
            return True
        except:
            actions = ActionChains(driver)
            actions.move_to_element(svg_element).click().perform()
            print(f"Выполнено: {action_name} [{context}]")
            time.sleep(0.5)
            return True
    except Exception as e:
        error_msg = f"Не удалось {action_name}: {e}"
        add_error_with_context(error_msg, context)
        return False


def click_reset_button(context=""):
    """Нажимает кнопку сброса по прямому селектору"""
    try:
        print(f"Сброс фильтра [{context}]...")

        # Используем прямой селектор кнопки сброса
        reset_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, FILTER_RESET_BUTTON_SELECTOR)
        ))

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reset_button)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", reset_button)
        print(f"Кнопка сброса нажата [{context}]")
        time.sleep(1)
        return True

    except Exception as e:
        error_msg = f"Ошибка при нажатии кнопки сброса: {e}"
        add_error_with_context(error_msg, context)
        return False


def select_all_records(context=""):
    print(f"Выбор всех записей [{context}]...")
    try:
        checkbox = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, CHECKBOX_ALL_SELECTOR)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", checkbox)
        print(f"Выбраны все записи [{context}]")
        time.sleep(2)
        return True
    except Exception as e:
        add_error_with_context(f"Не удалось выбрать все записи: {e}", context)
        return False


def click_element(by, selector, description, context="", timeout=10):
    try:
        element = wait.until(EC.element_to_be_clickable((by, selector)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
        element.click()
        print(f"Выполнено: {description} [{context}]")
        time.sleep(1)
        return True
    except Exception as e:
        add_error_with_context(f"Не удалось {description}: {e}", context)
        return False


def open_action_menu(context=""):
    print(f"Открытие меню 'Действие' [{context}]...")
    return click_element(By.CSS_SELECTOR, ACTION_BUTTON_SELECTOR, "Открыть меню 'Действие'", context)


def select_export_menu(context=""):
    print(f"Выбор пункта 'Экспорт' [{context}]...")
    return click_element(By.CSS_SELECTOR, EXPORT_MENU_ITEM_SELECTOR, "Выбрать пункт 'Экспорт'", context)


def select_export_type(export_type, context=""):
    print(f"Выбор типа экспорта: {export_type} [{context}]...")
    selector = EXPORT_BY_SELECTED_SELECTOR if export_type == "selected" else EXPORT_BY_FILTER_SELECTOR
    try:
        radio_element = driver.find_element(By.CSS_SELECTOR, selector)
        parent_label = radio_element.find_element(By.XPATH, "./..")
        if "ant-radio-button-checked" not in parent_label.get_attribute("class"):
            radio_element.click()
            print(f"Выбран тип: {'Выделенные' if export_type == 'selected' else 'По фильтру'} [{context}]")
            time.sleep(1)
        else:
            print(f"Уже выбран тип: {'Выделенные' if export_type == 'selected' else 'По фильтру'} [{context}]")
        return True
    except Exception as e:
        add_error_with_context(f"Не удалось выбрать тип экспорта: {e}", context)
        return False


def get_frontend_count(context=""):
    print(f"Получение количества записей с фронта [{context}]...")
    try:
        time.sleep(2)
        counter_element = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, COUNTER_MODAL_SELECTOR)
        ))
        for i in range(10):
            text = counter_element.text.strip()
            if text and "Загрузка" not in text and "loading" not in text.lower():
                numbers = re.findall(r'\d+', text.replace(',', ''))
                if numbers:
                    count = int(numbers[0])
                    print(f"Записей на фронте: {count} [{context}]")
                    return count
            time.sleep(0.5)
        print(f"Не удалось получить количество записей [{context}]")
        return 0
    except Exception as e:
        add_error_with_context(f"Ошибка при получении количества записей: {e}", context)
        return 0


def download_export_file(context=""):
    print(f"Загрузка файла экспорта [{context}]...")
    if not click_element(By.XPATH, EXPORT_DOWNLOAD_BUTTON, "Нажать кнопку 'Выгрузить'", context):
        return None
    time.sleep(3)
    print(f"Ожидание загрузки файла...")
    latest_file = wait_for_file_download("*.xlsx", timeout=60)
    if latest_file:
        return latest_file
    else:
        add_error_with_context(f"Файл не был загружен", context)
        return None


def read_excel_and_count_rows(file_path, context=""):
    try:
        print(f"Чтение файла: {os.path.basename(file_path)} [{context}]")
        df = read_excel_file_safe(file_path)
        total_rows = count_data_rows_in_excel(df)
        print(f"Строк данных в файле: {total_rows} [{context}]")
        return total_rows
    except Exception as e:
        add_error_with_context(f"Ошибка чтения Excel файла: {e}", context)
        return 0


def open_filter(context=""):
    print(f"Открытие фильтра [{context}]...")
    return click_svg_element(FILTER_OPEN_SELECTOR, "Открыть фильтр", context)


def select_random_ao(context=""):
    """Выбирает случайное АО в фильтре - ИСПРАВЛЕНО"""
    try:
        print(f"Выбор случайного АО в фильтре [{context}]...")
        global selected_ao_value

        # 1. Проверяем, что мы на нужном поле через label
        try:
            ao_label = driver.find_element(By.CSS_SELECTOR, AO_LABEL_SELECTOR)
            print(f"Найдена метка АО с текстом: '{ao_label.text}'")
        except:
            print("Метка АО не найдена, но продолжаем...")

        # 2. Находим контейнер поля АО (более надежный способ)
        # Ищем контейнер, который содержит input#aoCode
        ao_container = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'ant-select-selector') and .//input[@id='aoCode']]")
        ))

        if not ao_container:
            # Fallback: просто ищем контейнер
            ao_container = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.ant-select-selector")
            ))

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ao_container)
        time.sleep(0.5)

        # 3. Проверяем, что это именно поле АО (по плейсхолдеру или соседнему label)
        try:
            placeholder = driver.find_element(By.CSS_SELECTOR, ".ant-select-selection-placeholder")
            if placeholder and "Выберите значение" in placeholder.text:
                print("Поле содержит плейсхолдер 'Выберите значение'")
        except:
            pass

        # 4. Кликаем по контейнеру для открытия списка
        try:
            ao_container.click()
            print(f"Кликнули на контейнер АО")
        except:
            driver.execute_script("arguments[0].click();", ao_container)
            print(f"Кликнули на контейнер АО через JS")

        time.sleep(2)

        # 5. Ждем появления выпадающего списка
        dropdown_selectors = [
            "div.ant-select-dropdown:not(.ant-select-dropdown-hidden)",
            "div.ant-select-dropdown"
        ]

        dropdown = None
        for selector in dropdown_selectors:
            try:
                dropdown = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, selector)
                ))
                if dropdown and dropdown.is_displayed():
                    print(f"Выпадающий список открылся")
                    break
            except:
                continue

        if not dropdown:
            error_msg = "Не удалось открыть выпадающий список АО"
            add_error_with_context(error_msg, context)
            return False, None

        time.sleep(1)

        # 6. Собираем опции АО
        options = []
        option_elements = dropdown.find_elements(By.CSS_SELECTOR, "div.ant-select-item-option")

        for opt in option_elements:
            try:
                if opt.is_displayed():
                    opt_text = opt.text.strip()
                    # Исключаем "Выбрать все"
                    if opt_text and "Выбрать все" not in opt_text and "Select all" not in opt_text:
                        # Пробуем получить title (обычно там название АО)
                        title = opt.get_attribute("title")
                        if title and title not in ["Выбрать все", "Select all"]:
                            options.append((opt, title))
                            print(f"  Найдена опция: '{title}'")
                        elif opt_text:
                            options.append((opt, opt_text))
                            print(f"  Найдена опция: '{opt_text}'")
            except:
                continue

        print(f"Всего найдено опций АО для выбора: {len(options)}")

        if options:
            random_option, option_text = random.choice(options)
            print(f"Выбрано АО: '{option_text}'")

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", random_option)
            time.sleep(0.3)

            try:
                random_option.click()
            except:
                driver.execute_script("arguments[0].click();", random_option)

            selected_ao_value = option_text
            print(f"АО успешно выбрано: '{option_text}' [{context}]")
            time.sleep(1.5)
            return True, option_text
        else:
            error_msg = "Не найдено опций АО для выбора"
            add_error_with_context(error_msg, context)
            return False, None

    except Exception as e:
        error_msg = f"Общая ошибка при выборе АО: {str(e)[:200]}"
        add_error_with_context(error_msg, context)
        return False, None


def apply_filter(context=""):
    """Нажимает кнопку Применить в фильтре"""
    print(f"Применение фильтра [{context}]...")
    try:
        # Используем прямой селектор кнопки применения
        apply_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, FILTER_APPLY_BUTTON_SELECTOR)
        ))

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", apply_button)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", apply_button)
        print(f"Фильтр применен [{context}]")
        time.sleep(3)
        return True

    except Exception as e:
        # Fallback на старый метод
        try:
            button = driver.find_element(By.XPATH, "//button[contains(., 'Применить')]")
            button.click()
            print(f"Фильтр применен через XPath [{context}]")
            time.sleep(3)
            return True
        except:
            error_msg = f"Не удалось применить фильтр: {e}"
            add_error_with_context(error_msg, context)
            return False


def close_firefox_download_panel_system():
    """Закрывает панель загрузок Firefox через системные нажатия клавиш"""
    try:
        print("Попытка закрыть панель загрузок через системные клавиши...")

        # Импортируем pyautogui если доступен
        try:
            import pyautogui
            pyautogui_available = True
        except ImportError:
            pyautogui_available = False
            print("  pyautogui не установлен, пробуем другие методы")

        # Метод 1: pyautogui (самый надежный)
        if pyautogui_available:
            try:
                # Несколько раз нажимаем ESC для закрытия панели
                for _ in range(3):
                    pyautogui.press('esc')
                    time.sleep(0.2)
                print("  Отправлен ESC через pyautogui")
                time.sleep(1)
                return True
            except Exception as e:
                print(f"  Ошибка pyautogui: {e}")

        # Метод 2: Клавиши через Selenium Actions
        try:
            actions = ActionChains(driver)
            for _ in range(3):
                actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(0.2)
            print("  Отправлен ESC через Selenium Actions")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"  Ошибка Selenium Actions: {e}")

        return False
    except Exception as e:
        print(f"Ошибка при закрытии панели: {e}")
        return False


def ensure_download_panel_closed_system(max_attempts=3):
    """Многократно пытается закрыть панель загрузок через системные клавиши"""
    print("Убеждаемся, что панель загрузок закрыта (системный метод)...")

    for attempt in range(max_attempts):
        print(f"Попытка {attempt + 1}/{max_attempts} закрыть панель...")
        close_firefox_download_panel_system()
        time.sleep(1)

    print("Завершены попытки закрыть панель загрузок")
    return True


def perform_export_flow(export_type, context=""):
    print(f"\n{'='*50}")
    print(f"НАЧАЛО ЭКСПОРТА: {export_type.upper()} [{context}]")
    print(f"{'='*50}")

    result = {
        "export_type": export_type,
        "success": False,
        "frontend_count": 0,
        "file_rows": 0,
        "match": False,
        "file_path": None,
        "ao_value": selected_ao_value if export_type == "filter" else None
    }

    if not open_action_menu(context):
        return result

    if not select_export_menu(context):
        return result

    if not select_export_type(export_type, context):
        return result

    frontend_count = get_frontend_count(context)
    result["frontend_count"] = frontend_count

    file_path = download_export_file(context)
    if not file_path:
        return result

    result["file_path"] = file_path
    file_rows = read_excel_and_count_rows(file_path, context)
    result["file_rows"] = file_rows

    if frontend_count == file_rows:
        print(f"СОВПАДЕНИЕ: {file_rows} = {frontend_count} [{context}]")
        result["match"] = True
        result["success"] = True
    else:
        print(f"НЕ СОВПАДЕНИЕ: в файле {file_rows}, на фронте {frontend_count} [{context}]")
        add_error_with_context(f"Несовпадение количества записей: файл {file_rows}, фронт {frontend_count}", context)
        result["match"] = False
        result["success"] = False

    # После завершения экспорта принудительно закрываем панель загрузок
    ensure_download_panel_closed_system()

    return result


# ==================== ОСНОВНОЙ КОД ТЕСТА ====================

# 1. АВТОРИЗАЦИЯ
print("\n" + "="*50)
print("ШАГ 1: АВТОРИЗАЦИЯ")
print("="*50)

try:
    driver.get(URL)
    username_field = wait.until(EC.presence_of_element_located((By.ID, "normal_login_username")))
    username_field.send_keys(USERNAME)
    password_field = driver.find_element(By.ID, "normal_login_password")
    password_field.send_keys(PASSWORD)
    login_button = driver.find_element(By.CSS_SELECTOR, '.ant-btn.ant-btn-primary.w-100.mb-s')
    login_button.click()

    try:
        wait.until_not(EC.url_contains('login'))
        print("Авторизация успешна")
    except:
        current_url = driver.current_url
        if "login" not in current_url:
            print("Авторизация успешна")
        else:
            raise Exception("Остались на странице логина")

except Exception as e:
    add_error_with_context(f"Авторизация не удалась: {e}", "АВТОРИЗАЦИЯ")
    driver.quit()
    exit()

smart_wait_for_errors_disappear()
wait_for_page_load("После авторизации")

# 2. ПЕРЕХОД В РАЗДЕЛ
print("\n" + "="*50)
print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ")
print("="*50)

try:
    driver.get(SECTION_URL)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print(f"Переход в раздел '{SECTION_NAME}'")
    time.sleep(2)
    smart_wait_for_errors_disappear()
    wait_for_page_load("Переход в реестр водомеров")
except Exception as e:
    add_error_with_context(f"Не удалось перейти в раздел: {e}", "ПЕРЕХОД В РАЗДЕЛ")
    driver.quit()
    exit()

# 3. ЭКСПОРТ ПО ВЫДЕЛЕННЫМ
print("\n" + "="*50)
print("ШАГ 3: ЭКСПОРТ ПО ВЫДЕЛЕННЫМ")
print("="*50)

if select_all_records("ВЫБОР ВСЕХ ЗАПИСЕЙ"):
    result_selected = perform_export_flow("selected", "ЭКСПОРТ ПО ВЫДЕЛЕННЫМ")
    results_comparison["selected"] = result_selected
    smart_wait_for_errors_disappear()
    time.sleep(2)

# Очищаем папку перед следующим экспортом
if os.path.exists(DOWNLOAD_FOLDER):
    print(f"\nОчистка папки перед следующим экспортом...")
    for file in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, file)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                print(f"Удален файл: {file}")
            except:
                pass

# 4. РАБОТА С ФИЛЬТРОМ
print("\n" + "="*50)
print("ШАГ 4: РАБОТА С ФИЛЬТРОМ")
print("="*50)

print("Открытие фильтра...")
if click_svg_element(FILTER_OPEN_SELECTOR, "Открыть фильтр", "ОТКРЫТИЕ ФИЛЬТРА"):
    print("Фильтр открыт")
    time.sleep(2)
    smart_wait_for_errors_disappear()
else:
    add_error_with_context("Не удалось открыть фильтр", "ОТКРЫТИЕ ФИЛЬТРА")

# 4.1. Нажимаем кнопку сброса
click_reset_button("СБРОС ФИЛЬТРА")

# Проверяем ошибки после сброса
smart_wait_for_errors_disappear()
time.sleep(1)

# 4.2. Выбираем случайное АО
ao_success, ao_value = select_random_ao("ВЫБОР СЛУЧАЙНОГО АО")
if ao_success:
    print(f"АО выбрано успешно: '{ao_value}'")

    # 4.3. Применяем фильтр
    if apply_filter("ПРИМЕНЕНИЕ ФИЛЬТРА"):
        print("Фильтр применен успешно")
        smart_wait_for_errors_disappear()
        wait_for_page_load("После применения фильтра")

        # 5. ЭКСПОРТ ПО ФИЛЬТРУ
        print("\n" + "="*50)
        print("ШАГ 5: ЭКСПОРТ ПО ФИЛЬТРУ")
        print("="*50)

        result_filter = perform_export_flow("filter", "ЭКСПОРТ ПО ФИЛЬТРУ")
        if result_filter:
            results_comparison["filter"] = result_filter

        smart_wait_for_errors_disappear()
    else:
        add_error_with_context("Не удалось применить фильтр", "ПРИМЕНЕНИЕ ФИЛЬТРА")
else:
    add_error_with_context("Не удалось выбрать АО в фильтре", "ВЫБОР АО В ФИЛЬТРЕ")

# 6. ИТОГОВЫЙ ОТЧЕТ
print("\n" + "="*80)
print("ИТОГОВЫЙ ОТЧЕТ ПО ТЕСТИРОВАНИЮ")
print("="*80)

print(f"\nРАЗДЕЛ: {SECTION_NAME}")
print(f"URL: {SECTION_URL}")
print(f"Время выполнения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

print(f"\n{'='*40}")
print(f"РЕЗУЛЬТАТЫ ЭКСПОРТА")
print(f"{'='*40}")

test_passed = True

if "selected" in results_comparison:
    res = results_comparison["selected"]
    print(f"\nЭКСПОРТ ПО ВЫДЕЛЕННЫМ:")
    print(f"  Записей на фронте: {res['frontend_count']}")
    print(f"  Строк в файле: {res['file_rows']}")
    if res['file_path']:
        print(f"  Файл: {os.path.basename(res['file_path'])}")
    if res['match']:
        print(f"  Статус: СОВПАДАЕТ")
    else:
        print(f"  Статус: НЕ СОВПАДАЕТ")
        test_passed = False

if "filter" in results_comparison:
    res = results_comparison["filter"]
    print(f"\nЭКСПОРТ ПО ФИЛЬТРУ:")
    print(f"  Выбранное АО: {res['ao_value']}")
    print(f"  Записей на фронте: {res['frontend_count']}")
    print(f"  Строк в файле: {res['file_rows']}")
    if res['file_path']:
        print(f"  Файл: {os.path.basename(res['file_path'])}")
    if res['match']:
        print(f"  Статус: СОВПАДАЕТ")
    else:
        print(f"  Статус: НЕ СОВПАДАЕТ")
        test_passed = False

if not results_comparison:
    print("\nНе удалось выполнить ни одного экспорта")
    test_passed = False

print(f"\n{'='*40}")
print(f"ИТОГОВЫЙ ВЕРДИКТ")
print(f"{'='*40}")

if test_passed and not section_errors:
    print(f"\nТЕСТ ПРОЙДЕН УСПЕШНО")
    print(f"  Все проверки экспорта выполнены корректно")
    print(f"  Количество записей в файлах соответствует данным на фронте")
elif test_passed and section_errors:
    print(f"\nТЕСТ ПРОЙДЕН С ПРЕДУПРЕЖДЕНИЯМИ")
    print(f"  Экспорт работает корректно, но есть некритичные ошибки")
else:
    print(f"\nТЕСТ НЕ ПРОЙДЕН")
    print(f"  Обнаружены критические ошибки")

if section_errors:
    print(f"\n{'='*40}")
    print(f"НАЙДЕНО ОШИБОК: {len(section_errors)}")
    print(f"{'='*40}")

    errors_by_context = {}
    for error in section_errors:
        match = re.match(r'^\[(.*?)\]\s*(.*)$', error)
        if match:
            context = match.group(1)
            error_text = match.group(2)
            if context not in errors_by_context:
                errors_by_context[context] = []
            errors_by_context[context].append(error_text)
        else:
            if "БЕЗ КОНТЕКСТА" not in errors_by_context:
                errors_by_context["БЕЗ КОНТЕКСТА"] = []
            errors_by_context["БЕЗ КОНТЕКСТА"].append(error)

    for context, errors in errors_by_context.items():
        print(f"\n{context}:")
        print(f"   {'-' * (len(context) + 2)}")
        for i, error_text in enumerate(set(errors), 1):
            print(f"   {i}. {error_text}")
else:
    print(f"\nОШИБОК НЕ НАЙДЕНО")

print(f"\n{'='*40}")
print(f"ЗАГРУЖЕННЫЕ ФАЙЛЫ")
print(f"{'='*40}")

if os.path.exists(DOWNLOAD_FOLDER):
    files = os.listdir(DOWNLOAD_FOLDER)
    if files:
        print(f"\nПапка загрузки: {DOWNLOAD_FOLDER}")
        for file in files:
            file_path = os.path.join(DOWNLOAD_FOLDER, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"\n  {file}")
                print(f"    Размер: {size:,} байт")
                print(f"    Изменен: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"\nФайлы не загружены")
else:
    print(f"\nПапка не найдена: {DOWNLOAD_FOLDER}")

print(f"\n{'='*80}")
print(f"ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
print(f"{'='*80}")

try:
    print("\nЗакрытие браузера...")
    time.sleep(2)
    driver.quit()
    print("Браузер успешно закрыт")
except Exception as e:
    print(f"Не удалось закрыть браузер: {e}")