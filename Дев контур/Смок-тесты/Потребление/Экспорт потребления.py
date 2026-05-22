"""
ТЕСТ: Экспорт точек учета (Потребление) в Excel через веб-интерфейс "Предбиллинг"

Что тестирует:
1. Авторизация в системе
2. Переход в раздел "Точки учета (Потребление)"
3. Экспорт всех записей (по выделенным)
4. Работа с фильтром:
   - Выбор случайного АО
   - Применение фильтра
5. Экспорт отфильтрованных записей (по фильтру)
6. Сравнение количества записей в файле Excel с количеством на фронтенде
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

warnings.filterwarnings('ignore')

# Определяем папку для загрузки
DOWNLOAD_FOLDER = r"C:\Экспорт_потребление_ПБ"

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

print("=" * 60)
print("ТЕСТ РАЗДЕЛА: Экспорт точек учета (Потребление) в Excel")
print("=" * 60)

# Настройки для Firefox
firefox_options = Options()

# Пути к Firefox
firefox_paths = [
    r"C:\Program Files\Mozilla Firefox\firefox.exe",
    r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
]

# Ищем Firefox
firefox_found = False
firefox_path = ""
for path in firefox_paths:
    if os.path.exists(path):
        firefox_options.binary_location = path
        firefox_path = path
        print(f"Найден Firefox: {path}")
        firefox_found = True
        break

if not firefox_found:
    print("Firefox не найден в стандартных путях!")
    print("Пожалуйста, установите Firefox или проверьте путь")
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

# Опции для стабильности
firefox_options.set_preference("dom.webdriver.enabled", False)
firefox_options.set_preference('useAutomationExtension', False)
firefox_options.add_argument('--no-sandbox')
firefox_options.add_argument('--disable-dev-shm-usage')
firefox_options.add_argument('--disable-gpu')

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

# ============================================
# СЕЛЕКТОРЫ
# ============================================

# Основные селекторы
FILTER_SELECTOR = "svg[data-icon='filter']"
APPLY_BUTTON_SELECTOR = "div.filterOperations > button:nth-child(1)"
RESET_BUTTON_SELECTOR = "div.filterOperations > button:nth-child(2)"
APPLY_SVG_FALLBACK = "svg[data-icon='check']"
RESET_SVG_FALLBACK = "svg[data-icon='stop']"

# Селекторы таблицы
TABLE_SELECTOR = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body"
CHECKBOX_SELECTOR = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__header > div > div > div:nth-child(1) > label > span > input"

# Селекторы для работы с экспортом
ACTION_MENU_SELECTOR = "#root > section > section > div > div.ant-space.ant-space-horizontal.ant-space-align-center > div > div > div > div > div > button > div > div:nth-child(1) > span > svg"
EXPORT_MENU_ITEM_SELECTOR = "html > div > div > div > ul > li:nth-child(3) > span > button"  # Индекс 3 для потребления

# Селекторы для выбора типа экспорта
SELECTED_TYPE_SELECTOR = "#statusChoose > label:nth-child(2)"  # "Выделенные"
FILTER_TYPE_SELECTOR = "#statusChoose > label:nth-child(1)"   # "По фильтру"

# Селектор для счетчика в окне экспорта
COUNTER_SELECTOR = "div.flexStart.counterTextModal"

# Селекторы для кнопки выгрузки
DOWNLOAD_BUTTON_SELECTOR = "button[type='submit'][label='Выгрузить']"  # По атрибутам
CANCEL_BUTTON_SELECTOR = "button[type='button'][label='Отмена']"      # Для отмены, если понадобится

# Альтернативные селекторы (на случай, если атрибуты не сработают)
DOWNLOAD_BUTTON_TEXT_SELECTOR = "//button[contains(text(), 'Выгрузить')]"
DOWNLOAD_BUTTON_CLASS_SELECTOR = "button.ant-btn.ant-btn-primary"

# Селектор для поля АО в фильтре
AO_INPUT_SELECTOR = "input#aoDistrictCode[type='search']"

# ============================================
# ХРАНЕНИЕ ОШИБОК И РЕЗУЛЬТАТОВ
# ============================================

error_log = {
    "total_errors_found": 0,
    "errors_closed": 0,
    "errors_details": []
}

current_action_context = "Начало теста"
results_comparison = {}
selected_ao_value = None


# ============================================
# ФУНКЦИИ ДЛЯ УМНОГО ОЖИДАНИЯ И ЗАКРЫТИЯ ОШИБОК
# ============================================

def add_error_with_context(error_text, context):
    """Добавляет ошибку с контекстом где она произошла"""
    full_error = f"[{context}] {error_text}"
    error_log["total_errors_found"] += 1
    error_log["errors_details"].append({
        "time": time.strftime("%H:%M:%S"),
        "context": context,
        "text": error_text
    })
    print(f"ОШИБКА: {full_error}")
    return error_log


def smart_wait_for_errors_disappear():
    """Умное ожидание исчезновения ошибок на странице с возможностью закрытия"""
    print(f"Ожидание исчезновения ошибок...")

    start_wait_time = time.time()
    max_wait_time = 5

    def try_close_error():
        """Пытается закрыть ошибку по крестику"""
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
                                print(f"  Найден и кликнут крестик")
                                error_log["errors_closed"] += 1
                                time.sleep(0.2)
                                return True
                        except:
                            try:
                                driver.execute_script("arguments[0].click();", btn)
                                print(f"  Кликнут крестик через JS")
                                error_log["errors_closed"] += 1
                                time.sleep(0.2)
                                return True
                            except:
                                continue
                except:
                    continue
            return False
        except Exception as e:
            print(f"  Ошибка при попытке закрыть ошибку: {e}")
            return False

    def check_for_persistent_errors():
        """Проверяет наличие стойких ошибок"""
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
                                        "успешно" not in text_lower):
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
                    print(f"  Ошибка держится {elapsed:.1f}с, пробуем закрыть...")
                    if try_close_error():
                        print(f"  Попытка закрытия выполнена")
                        time.sleep(0.5)
                    else:
                        print(f"  Не удалось найти кнопку закрытия")
                time.sleep(0.5)
            else:
                return True
        return False
    except Exception as e:
        print(f"Исключение в умном ожидании: {e}")
        return False


def wait_for_page_load(context=""):
    """Ожидание полной загрузки страницы"""
    global current_action_context
    if context:
        current_action_context = f"Загрузка страницы: {context}"

    print(f"Ожидание загрузки данных [{context}]...")
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
        print(f"Загрузка данных завершена за {load_duration:.1f} секунд")
        smart_wait_for_errors_disappear()
        return load_duration

    except Exception as e:
        print(f"  Ошибка при ожидании загрузки: {e}")
        smart_wait_for_errors_disappear()
        return time.time() - load_start


def close_firefox_download_panel():
    """Закрывает панель загрузок Firefox"""
    try:
        print("Закрытие панели загрузок Firefox...")

        # Пробуем закрыть через нажатие ESC
        try:
            actions = ActionChains(driver)
            actions.send_keys(Keys.ESCAPE).perform()
            print("Нажата клавиша ESC для закрытия панели загрузок")
            time.sleep(1)
            return True
        except:
            pass

        # Пробуем через JavaScript
        js_code = """
        var downloadPanels = document.querySelectorAll('[class*="download"], [id*="download"], panel[type="autocomplete-richlistbox"]');
        for (var i = 0; i < downloadPanels.length; i++) {
            var panel = downloadPanels[i];
            if (panel.style && panel.style.visibility !== 'hidden') {
                panel.style.visibility = 'hidden';
                panel.style.display = 'none';
            }
        }

        var closeButtons = document.querySelectorAll('[aria-label="Close"], .close-button, [title="Close"]');
        for (var i = 0; i < closeButtons.length; i++) {
            try {
                closeButtons[i].click();
            } catch(e) {}
        }

        return true;
        """

        result = driver.execute_script(js_code)
        print("Панель загрузок скрыта через JavaScript")
        return result

    except Exception as e:
        print(f"Не удалось закрыть панель загрузок: {e}")
        return False


def wait_for_file_download(filename_pattern="Реестр*Потребление*.xlsx", timeout=60):
    """Ожидает загрузку файла по шаблону"""
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

                    if file_size > 100:
                        with open(latest_file, 'rb') as f:
                            header = f.read(100)

                        if b'PK' in header[:2] or file_size > 1024:
                            print(f"Файл найден: {os.path.basename(latest_file)}")
                            print(f"Размер: {file_size} байт")
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
    """Безопасное чтение Excel файла"""
    try:
        file_size = os.path.getsize(file_path)

        if file_size < 100:
            return pd.DataFrame()

        engines = [
            ('openpyxl', 'openpyxl'),
            ('xlrd', 'xlrd'),
        ]

        file_ext = os.path.splitext(file_path)[1].lower()

        for engine_name, engine in engines:
            try:
                if file_ext == '.xlsx':
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


def click_svg_element(svg_selector, action_name, context=""):
    """Кликает на SVG элемент"""
    global current_action_context
    if context:
        current_action_context = context
    else:
        current_action_context = f"Клик на SVG: {action_name}"

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
            print(f"✓ {action_name}")
            time.sleep(0.5)
            smart_wait_for_errors_disappear()
            return True
        except:
            actions = ActionChains(driver)
            actions.move_to_element(svg_element).click().perform()
            print(f"✓ {action_name}")
            time.sleep(0.5)
            smart_wait_for_errors_disappear()
            return True

    except Exception as e:
        error_msg = f"Не удалось {action_name}: {e}"
        add_error_with_context(error_msg, context)
        return False


def click_element(selector, element_name, context=""):
    """Кликает на элемент по селектору"""
    global current_action_context
    if context:
        current_action_context = context
    else:
        current_action_context = f"Клик на '{element_name}'"

    try:
        element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", element)
        print(f"✓ {element_name}")
        time.sleep(0.5)
        smart_wait_for_errors_disappear()
        return True
    except Exception as e:
        print(f"✗ Не удалось кликнуть на {element_name}: {e}")
        smart_wait_for_errors_disappear()
        return False


def select_all_checkbox():
    """Выбирает все записи через чекбокс в заголовке таблицы"""
    global current_action_context
    current_action_context = "Выбор всех записей через чекбокс"

    try:
        checkbox = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, CHECKBOX_SELECTOR))
        )

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
        time.sleep(0.5)

        driver.execute_script("arguments[0].click();", checkbox)
        print("✓ Все записи выбраны через чекбокс")
        time.sleep(2)

        smart_wait_for_errors_disappear()
        return True

    except Exception as e:
        error_msg = f"Не удалось выбрать все записи: {e}"
        add_error_with_context(error_msg, "ВЫБОР ВСЕХ ЗАПИСЕЙ")
        return False


def open_filter():
    """Открывает фильтр"""
    return click_svg_element(FILTER_SELECTOR, "Открыть фильтр", "ОТКРЫТИЕ ФИЛЬТРА")


def reset_filter():
    """Сбрасывает фильтр"""
    try:
        print("\nСбрасываем фильтр...")
        try:
            reset_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, RESET_BUTTON_SELECTOR))
            )
            reset_button.click()
            print("✓ Фильтр сброшен")
        except:
            reset_svg = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, RESET_SVG_FALLBACK))
            )
            parent_button = reset_svg.find_element(By.XPATH, "..")
            parent_button.click()
            print("✓ Фильтр сброшен (по иконке)")

        time.sleep(1)
        wait_for_page_load("после сброса фильтра")
        return True
    except Exception as e:
        print(f"✗ Не удалось сбросить фильтр: {e}")
        return False


def apply_filter():
    """Применяет фильтр"""
    try:
        print("\nПрименяем фильтр...")
        try:
            apply_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, APPLY_BUTTON_SELECTOR))
            )
            apply_button.click()
            print("✓ Фильтр применен")
        except:
            apply_svg = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, APPLY_SVG_FALLBACK))
            )
            parent_button = apply_svg.find_element(By.XPATH, "..")
            parent_button.click()
            print("✓ Фильтр применен (по иконке)")

        time.sleep(2)
        wait_for_page_load("после применения фильтра")
        return True
    except Exception as e:
        print(f"✗ Не удалось применить фильтр: {e}")
        return False


def select_random_ao():
    """Выбирает случайное АО в фильтре"""
    global current_action_context, selected_ao_value
    current_action_context = "Выбор случайного АО в фильтре"

    try:
        print("Выбор случайного АО в фильтре...")

        # Находим поле АО по ID
        ao_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, AO_INPUT_SELECTOR))
        )
        print("✓ Найдено поле АО")

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ao_input)
        time.sleep(0.5)

        # Кликаем на родительский селектор
        parent_selector = ao_input.find_element(By.XPATH, "./ancestor::div[contains(@class, 'ant-select-selector')]")
        parent_selector.click()
        print("  Открыли выпадающий список")
        time.sleep(1)

        # Ждем появления списка
        dropdown = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ant-select-dropdown:not(.ant-select-dropdown-hidden)"))
        )

        # Ищем опции
        options = dropdown.find_elements(By.CSS_SELECTOR, ".ant-select-item-option")
        print(f"  Найдено опций АО: {len(options)}")

        if not options:
            add_error_with_context("Не найдено опций АО для выбора", current_action_context)
            return False

        # Фильтруем опции
        valid_options = []
        for option in options:
            try:
                option_text = option.text.strip()
                if "Выбрать все" not in option_text and option_text:
                    valid_options.append(option)
            except:
                continue

        if not valid_options:
            add_error_with_context("Нет доступных значений АО", current_action_context)
            return False

        # Выбираем случайное значение
        random_option = random.choice(valid_options)
        option_text = random_option.text.strip()
        random_option.click()
        print(f"✓ Выбрано АО: '{option_text}'")

        selected_ao_value = option_text
        time.sleep(1)
        smart_wait_for_errors_disappear()
        return True

    except Exception as e:
        add_error_with_context(f"Ошибка при выборе АО: {e}", current_action_context)
        return False


def get_export_frontend_count():
    """Получает количество записей с фронта в окне экспорта"""
    global current_action_context
    current_action_context = "Получение количества записей с фронта"

    try:
        time.sleep(2)

        counter_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, COUNTER_SELECTOR))
        )
        counter_text = counter_element.text.strip()
        print(f"Текст счетчика: '{counter_text}'")

        numbers = re.findall(r'\d+', counter_text.replace(',', '').replace(' ', ''))
        if numbers:
            count = int(numbers[0])
            print(f"✓ Количество записей на фронте: {count}")
            return count
        else:
            if "Всего 0" in counter_text or "0 записей" in counter_text:
                print("На фронте 0 записей")
                return 0

        return 0

    except Exception as e:
        add_error_with_context(f"Не удалось получить количество записей: {e}", current_action_context)
        return 0


def count_data_rows_in_excel(df):
    """Считает только строки с данными, пропуская заголовки"""
    if df.empty:
        return 0

    HEADER_ROWS = 2

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
                    if len(cell_str) > 0:
                        row_has_data = True
                        break

        if row_has_data:
            data_rows += 1

    print(f"Всего строк в файле: {len(df)}, строк заголовка: {HEADER_ROWS}, строк данных: {data_rows}")
    return data_rows


def perform_export(export_type="selected", context=""):
    """Выполняет экспорт точек учета"""
    try:
        print(f"\n--- Выполнение экспорта: {export_type} [{context}] ---")

        # 1. Открываем меню "Действие"
        if not click_svg_element(ACTION_MENU_SELECTOR, "Открыть меню 'Действие'", context):
            add_error_with_context(f"Не удалось открыть меню 'Действие'", context)
            return None

        print(f"Меню 'Действие' открыто")
        time.sleep(2)

        # 2. Выбираем "Экспорт" (индекс 3 для потребления)
        if not click_element(EXPORT_MENU_ITEM_SELECTOR, "Выбрать пункт 'Экспорт'", context):
            add_error_with_context(f"Не удалось выбрать 'Экспорт'", context)
            return None

        time.sleep(2)

        # 3. Выбираем тип экспорта
        try:
            if export_type == "selected":
                click_element(SELECTED_TYPE_SELECTOR, "Выбрать 'Выделенные'", context)
            elif export_type == "filter":
                click_element(FILTER_TYPE_SELECTOR, "Выбрать 'По фильтру'", context)
        except Exception as e:
            add_error_with_context(f"Не удалось выбрать тип экспорта: {e}", context)

        time.sleep(1)

        # 4. Получаем количество записей с фронта
        frontend_count = get_export_frontend_count()
        print(f"Количество записей на фронте для экспорта {export_type}: {frontend_count}")

        # 5. Нажимаем кнопку "Выгрузить" (несколько способов для надежности)
        try:
            print("Нажатие кнопки 'Выгрузить'...")
            time.sleep(1)

            # Способ 1: По атрибутам label и type (самый надежный из HTML)
            try:
                download_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, DOWNLOAD_BUTTON_SELECTOR))
                )
                driver.execute_script("arguments[0].click();", download_button)
                print("✓ Кнопка 'Выгрузить' нажата (по атрибутам)")
            except:
                # Способ 2: По тексту кнопки
                download_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, DOWNLOAD_BUTTON_TEXT_SELECTOR))
                )
                driver.execute_script("arguments[0].click();", download_button)
                print("✓ Кнопка 'Выгрузить' нажата (по тексту)")

            time.sleep(5)
        except Exception as e:
            add_error_with_context(f"Не удалось нажать кнопку 'Выгрузить': {e}", context)
            return None

        # 6. Ожидаем загрузку файла
        latest_file = wait_for_file_download("Реестр*Потребление*.xlsx", timeout=45)

        if not latest_file:
            latest_file = wait_for_file_download("*.xlsx", timeout=15)

        if latest_file:
            print(f"✓ Файл загружен: {os.path.basename(latest_file)}")

            df = read_excel_file_safe(latest_file)
            data_rows = count_data_rows_in_excel(df)

            print(f"Файл содержит {data_rows} строк данных")

            if data_rows == frontend_count:
                print(f"✓ СОВПАДЕНИЕ: Данные в файле ({data_rows}) совпадают с фронтом ({frontend_count})")
                match_status = "СОВПАДАЕТ"
            else:
                print(f"✗ НЕ СОВПАДЕНИЕ: Данные в файле ({data_rows}) не совпадают с фронтом ({frontend_count})")
                match_status = "НЕ СОВПАДАЕТ"

            return {
                "file": latest_file,
                "data_rows": data_rows,
                "frontend_count": frontend_count,
                "export_type": export_type,
                "context": context,
                "match_status": match_status
            }
        else:
            add_error_with_context("Файл не был загружен", context)
            return None

    except Exception as e:
        add_error_with_context(f"Ошибка при выполнении экспорта {export_type}: {e}", context)
        return None


# ============================================
# ОСНОВНОЙ КОД ТЕСТА
# ============================================

# 1. АВТОРИЗАЦИЯ
print("\n" + "=" * 50)
print("ШАГ 1: АВТОРИЗАЦИЯ")
print("=" * 50)

try:
    current_action_context = "Авторизация"
    driver.get(URL)
    username_field = wait.until(EC.presence_of_element_located((By.ID, "normal_login_username")))
    username_field.send_keys(USERNAME)
    password_field = driver.find_element(By.ID, "normal_login_password")
    password_field.send_keys(PASSWORD)
    login_button = driver.find_element(By.CSS_SELECTOR, '.ant-btn.ant-btn-primary.w-100.mb-s')
    login_button.click()
    wait.until_not(EC.url_contains('login'))
    print("✓ Авторизация успешна")
    smart_wait_for_errors_disappear()
except Exception as e:
    print(f"✗ Авторизация не удалась: {e}")
    driver.quit()
    exit()

# 2. ПЕРЕХОД В РАЗДЕЛ
print("\n" + "=" * 50)
print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ 'ТОЧКИ УЧЕТА (ПОТРЕБЛЕНИЕ)'")
print("=" * 50)

try:
    current_action_context = "Переход в раздел"
    section_url = 'http://10.5.121.74/technicalControl/meteringPointsPredBill'
    driver.get(section_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("✓ Переход в раздел")
    time.sleep(2)
    smart_wait_for_errors_disappear()
    wait_for_page_load("после перехода")
except Exception as e:
    print(f"✗ Не удалось перейти в раздел: {e}")
    driver.quit()
    exit()

# 3. ПЕРВЫЙ ЭКСПОРТ: ПО ВЫДЕЛЕННЫМ
print("\n" + "=" * 50)
print("ШАГ 3: ЭКСПОРТ ПО ВЫДЕЛЕННЫМ")
print("=" * 50)

# 3.1. Выбираем все записи через чекбокс
select_all_checkbox()

# 3.2. Выполняем экспорт по выделенным
export_selected_result = perform_export("selected", "ЭКСПОРТ ПО ВЫДЕЛЕННЫМ")
if export_selected_result:
    results_comparison["selected"] = export_selected_result
time.sleep(1)

smart_wait_for_errors_disappear()
close_firefox_download_panel()

# Очищаем папку перед следующим экспортом
if os.path.exists(DOWNLOAD_FOLDER):
    print(f"\nОчистка папки перед экспортом по фильтру: {DOWNLOAD_FOLDER}")
    for file in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, file)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                print(f"Удален файл: {file}")
            except:
                pass

# 4. РАБОТА С ФИЛЬТРОМ
print("\n" + "=" * 50)
print("ШАГ 4: РАБОТА С ФИЛЬТРОМ")
print("=" * 50)

# 4.1. Открываем фильтр
if open_filter():
    time.sleep(2)
    smart_wait_for_errors_disappear()

    # 4.2. Сбрасываем фильтр
    reset_filter()
    time.sleep(1)
    smart_wait_for_errors_disappear()

    # 4.3. Выбираем случайное АО
    if select_random_ao():
        print("✓ АО выбрано успешно")
        time.sleep(1)

        # 4.4. Применяем фильтр
        if apply_filter():
            smart_wait_for_errors_disappear()
            wait_for_page_load("после применения фильтра")

            # 5. ЭКСПОРТ ПО ФИЛЬТРУ
            print("\n" + "=" * 50)
            print("ШАГ 5: ЭКСПОРТ ПО ФИЛЬТРУ")
            print("=" * 50)

            export_filter_result = perform_export("filter", "ЭКСПОРТ ПО ФИЛЬТРУ")
            if export_filter_result:
                results_comparison["filter"] = export_filter_result

            smart_wait_for_errors_disappear()
            close_firefox_download_panel()
        else:
            add_error_with_context("Не удалось применить фильтр", "ПРИМЕНЕНИЕ ФИЛЬТРА")
    else:
        add_error_with_context("Не удалось выбрать АО", "ВЫБОР АО")
else:
    add_error_with_context("Не удалось открыть фильтр", "ОТКРЫТИЕ ФИЛЬТРА")

# 6. ИТОГОВЫЙ ОТЧЕТ
print("\n" + "=" * 80)
print("ИТОГОВЫЙ ОТЧЕТ")
print("=" * 80)

print(f"\nИТОГ ПРОВЕРКИ ЭКСПОРТА ТОЧЕК УЧЕТА:")

test_passed = True

if "selected" in results_comparison:
    result = results_comparison["selected"]
    print(f"\nЭКСПОРТ ПО ВЫДЕЛЕННЫМ:")
    print(f"  Файл: {os.path.basename(result['file'])}")
    print(f"  Строк данных в файле: {result['data_rows']}")
    print(f"  Записей на фронте: {result['frontend_count']}")
    print(f"  Статус: {result['match_status']}")

    if result['match_status'] == "НЕ СОВПАДАЕТ":
        test_passed = False

if "filter" in results_comparison:
    result = results_comparison["filter"]
    print(f"\nЭКСПОРТ ПО ФИЛЬТРУ:")
    print(f"  Файл: {os.path.basename(result['file'])}")
    print(f"  Строк данных в файле: {result['data_rows']}")
    print(f"  Записей на фронте: {result['frontend_count']}")
    print(f"  Статус: {result['match_status']}")

    if result['match_status'] == "НЕ СОВПАДАЕТ":
        test_passed = False

if not results_comparison:
    print("\n⚠ Не удалось выполнить ни одного экспорта")
    test_passed = False

print(f"\nИНФОРМАЦИЯ ОБ ОШИБКАХ:")
print(f"  • Всего ошибок найдено: {error_log['total_errors_found']}")
print(f"  • Успешно закрыто: {error_log['errors_closed']}")

if error_log['errors_details']:
    print(f"  • Детали ошибок:")
    for i, err in enumerate(error_log['errors_details'], 1):
        print(f"    {i}. [{err['time']}] {err['context']}")
        print(f"       {err['text']}")

print(f"\nРЕЗУЛЬТАТ ТЕСТА: {'✓ ПРОЙДЕН' if test_passed else '✗ НЕ ПРОЙДЕН'}")
print("=" * 80)

# Закрытие браузера
try:
    print("\nЗакрытие браузера...")
    time.sleep(2)
    driver.quit()
    print("✓ Браузер успешно закрыт")
except Exception as e:
    print(f"✗ Не удалось закрыть браузер: {e}")