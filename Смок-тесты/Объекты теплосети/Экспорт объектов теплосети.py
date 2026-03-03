"""
ТЕСТ: Экспорт объектов теплосети в Excel через веб-интерфейс "Предбиллинг"

Что тестирует:
1. Авторизация в системе
2. Переход в раздел "Объекты теплосети"
3. Экспорт всех объектов (по выделенным)
4. Работа с фильтром:
   - Сброс фильтра
   - Выбор случайного АО
   - Применение фильтра
5. Экспорт отфильтрованных объектов (по фильтру)
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
import time
import os
import pandas as pd
import glob
import re
import random
import warnings

warnings.filterwarnings('ignore')

# Определяем папку для загрузки
DOWNLOAD_FOLDER = r"C:\Экспорт_объекты_теплосети_ПБ"

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
print("ТЕСТ РАЗДЕЛА: Экспорт объектов теплосети в Excel")
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
    from webdriver_manager.firefox import GeckoDriverManager

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

# Хранение ошибок с контекстом
section_errors = []
results_comparison = {}  # Для хранения результатов сравнения


def add_error_with_context(error_text, context):
    """Добавляет ошибку с контекстом где она произошла"""
    full_error = f"[{context}] {error_text}"
    if full_error not in section_errors:
        section_errors.append(full_error)
        print(f"ОШИБКА: {full_error}")
    return section_errors


def smart_wait_for_errors_disappear():
    """Умное ожидание исчезновения ошибок на странице с возможностью закрытия"""
    print(f"Ожидание исчезновения ошибок...")

    start_wait_time = time.time()
    max_wait_time = 5

    def try_close_error():
        """Пытается закрыть ошибку по крестику"""
        try:
            # Ищем кнопки закрытия ошибок
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
        except Exception as e:
            print(f"Ошибка при попытке закрыть ошибку: {e}")
            return False

    def check_for_persistent_errors():
        """Проверяет наличие стойких ошибок, которые можно закрыть"""
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
    """Ожидание полной загрузки страницы с отслеживанием времени"""
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


def wait_for_file_download(filename_pattern="Объекты*теплосети*.xlsx", timeout=60):
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

                    if file_size > 100:  # Минимальный размер файла
                        with open(latest_file, 'rb') as f:
                            header = f.read(100)

                        if b'PK' in header[:2] or file_size > 1024:  # Excel файл или любой файл > 1KB
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
    """Безопасное чтение Excel файла - считаем только строки с данными (без заголовков)"""
    try:
        file_size = os.path.getsize(file_path)

        if file_size < 100:  # Минимальный размер
            return pd.DataFrame()  # Возвращаем пустой DataFrame

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


def select_all_checkbox_objects(context=""):
    """Выбирает все объекты через чекбокс в заголовке таблицы"""
    try:
        print(f"Выбор всех объектов через чекбокс [{context}]...")

        # Селектор чекбокса для объектов теплосети
        checkbox_selector = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__header > div > div > div:nth-child(1) > label > span > input"

        checkbox = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, checkbox_selector))
        )

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
        time.sleep(0.5)

        # Кликаем через JavaScript для надежности
        driver.execute_script("arguments[0].click();", checkbox)
        print("✓ Все объекты выбраны через чекбокс")
        time.sleep(2)

        # Проверяем, что чекбокс выбран
        is_checked = driver.execute_script("return arguments[0].checked;", checkbox)
        if is_checked:
            print("  Чекбокс успешно установлен")
        else:
            print("  ⚠ Чекбокс не установлен, пробуем еще раз...")
            checkbox.click()
            time.sleep(1)

        smart_wait_for_errors_disappear()
        return True

    except Exception as e:
        error_msg = f"Не удалось выбрать все объекты: {e}"
        add_error_with_context(error_msg, context)

        # Пробуем альтернативный способ
        try:
            print("Пробуем альтернативный способ...")
            label_selector = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__header > div > div > div:nth-child(1) > label"
            label = driver.find_element(By.CSS_SELECTOR, label_selector)
            driver.execute_script("arguments[0].click();", label)
            print("✓ Все объекты выбраны через label")
            time.sleep(2)
            return True
        except Exception as e2:
            error_msg = f"Альтернативный способ тоже не сработал: {e2}"
            add_error_with_context(error_msg, context)
            return False


def open_filter_objects(context=""):
    """Открывает фильтр объектов теплосети"""
    try:
        print(f"Открытие фильтра объектов [{context}]...")
        filter_selector = "svg[data-icon='filter']"
        return click_svg_element(filter_selector, "Открыть фильтр", context)
    except Exception as e:
        error_msg = f"Не удалось открыть фильтр: {e}"
        add_error_with_context(error_msg, context)
        return False


def reset_filter_objects(context=""):
    """Сбрасывает фильтр объектов теплосети"""
    try:
        print(f"Сброс фильтра объектов [{context}]...")
        reset_selector = "svg[data-icon='stop']"
        return click_svg_element(reset_selector, "Сбросить фильтр", context)
    except Exception as e:
        error_msg = f"Не удалось сбросить фильтр: {e}"
        add_error_with_context(error_msg, context)
        return False


def select_random_ao_objects(context=""):
    """Выбирает случайное АО в фильтре объектов теплосети"""
    try:
        print(f"Выбор случайного АО в фильтре объектов [{context}]...")

        # Ищем поле АО по ID
        try:
            ao_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input#aoDistrictCode[type='search']"))
            )
            print(f"Найдено поле АО по ID: aoDistrictCode")
        except:
            ao_selectors = [
                "#aoDistrictCode",
                "input[id='aoDistrictCode']",
                "input.ant-select-selection-search-input",
                "div.ant-select-selector input"
            ]

            ao_input = None
            for selector in ao_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        try:
                            element_id = element.get_attribute("id") or ""
                            if "aoDistrictCode" in element_id:
                                ao_input = element
                                print(f"Найдено поле АО: {selector}")
                                break
                        except:
                            continue
                    if ao_input:
                        break
                except:
                    continue

        if not ao_input:
            error_msg = "Поле АО не найдено в фильтре объектов"
            add_error_with_context(error_msg, context)
            return False

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ao_input)
        time.sleep(0.5)

        # Кликаем на поле для открытия списка
        try:
            parent_selector = ao_input.find_element(By.XPATH, "./ancestor::div[contains(@class, 'ant-select-selector')]")
            parent_selector.click()
            print(f"Кликнули на родительский div поля АО")
        except:
            try:
                ao_input.click()
                print(f"Кликнули на поле АО")
            except Exception as e2:
                error_msg = f"Не удалось кликнуть на поле АО: {e2}"
                add_error_with_context(error_msg, context)
                return False

        time.sleep(1.5)

        # Ищем опции АО
        options = []
        option_selectors = [
            "div.ant-select-item-option[title]",
            "div.ant-select-item-option",
            "div[role='option']",
            "li.ant-select-item-option"
        ]

        for selector in option_selectors:
            try:
                found_options = driver.find_elements(By.CSS_SELECTOR, selector)
                for option in found_options:
                    try:
                        option_text = option.text.strip()
                        if option_text and "Выбрать все" not in option_text and "Select all" not in option_text:
                            options.append((option, option_text))
                    except:
                        continue
                if options:
                    print(f"Найдено опций АО: {len(options)}")
                    break
            except:
                continue

        if not options:
            try:
                xpath_options = driver.find_elements(By.XPATH,
                    "//div[contains(@class, 'ant-select-item-option') and "
                    "not(contains(@class, 'ant-select-item-option-select-all')) and "
                    "not(contains(text(), 'Выбрать все')) and "
                    "not(contains(text(), 'Select all'))]"
                )

                for option in xpath_options:
                    try:
                        option_text = option.text.strip()
                        if option_text:
                            options.append((option, option_text))
                    except:
                        continue

                if xpath_options:
                    print(f"Найдено опций АО по XPath: {len(options)}")
            except:
                pass

        print(f"Всего найдено опций АО для выбора: {len(options)}")

        if len(options) > 0:
            random_option, option_text = random.choice(options)
            print(f"Попытка выбрать АО: '{option_text}'")

            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", random_option)
                time.sleep(0.3)
            except:
                pass

            try:
                random_option.click()
                print(f"✓ Выбрано случайное АО: '{option_text}'")
                time.sleep(1)
                return True
            except:
                try:
                    driver.execute_script("arguments[0].click();", random_option)
                    print(f"✓ Выбрано случайное АО через JS: '{option_text}'")
                    time.sleep(1)
                    return True
                except Exception as e2:
                    error_msg = f"Не удалось выбрать АО '{option_text}': {e2}"
                    add_error_with_context(error_msg, context)
                    return False
        else:
            error_msg = "Не найдено опций АО для выбора"
            add_error_with_context(error_msg, context)
            return False

    except Exception as e:
        error_msg = f"Общая ошибка при выборе АО: {str(e)[:200]}"
        add_error_with_context(error_msg, context)
        return False


def apply_filter_objects(context=""):
    """Нажимает кнопку Применить в фильтре объектов теплосети"""
    try:
        print(f"Применение фильтра объектов [{context}]...")

        # Ищем кнопку Применить по атрибуту section
        try:
            apply_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[section='accountingObjectsPredBill']"))
            )
            apply_button.click()
            print(f"✓ Найдена и нажата кнопка по атрибуту section [{context}]")
            time.sleep(3)
            return True
        except:
            pass

        # Пробуем через JavaScript
        button = driver.execute_script("""
            var buttons = document.querySelectorAll('button[section="accountingObjectsPredBill"]');
            if (buttons.length > 0) return buttons[0];
            
            buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                var btn = buttons[i];
                if (btn.querySelector('svg[data-icon="check"]') || 
                    btn.querySelector('.anticon-check')) {
                    return btn;
                }
            }
            return null;
        """)

        if button:
            driver.execute_script("arguments[0].click();", button)
            print(f"✓ Фильтр применен через JavaScript [{context}]")
            time.sleep(3)
            return True

        error_msg = "Не удалось найти кнопку 'Применить' в фильтре объектов"
        add_error_with_context(error_msg, context)
        return False

    except Exception as e:
        error_msg = f"Ошибка при применении фильтра объектов: {str(e)[:150]}"
        add_error_with_context(error_msg, context)
        return False


def perform_export_objects(export_type="selected", context=""):
    """
    Выполняет экспорт объектов теплосети
    export_type: "selected" - по выделенным, "filter" - по фильтру
    """
    try:
        print(f"\n--- Выполнение экспорта объектов: {export_type} [{context}] ---")

        # 1. Открываем меню "Действие"
        action_button_selector = "#root > section > section > div > div.ant-space.ant-space-horizontal.ant-space-align-center > div > div > div > div > div > button > div > div:nth-child(1) > span > svg"

        if not click_svg_element(action_button_selector, "Открыть меню 'Действие'", context):
            add_error_with_context(f"Не удалось открыть меню 'Действие' для экспорта {export_type}", context)
            return None

        print(f"Меню 'Действие' открыто [{context}]")
        time.sleep(2)

        # 2. Выбираем "Экспорт" (индекс 4 для объектов теплосети)
        export_selector = "html > div > div > div > ul > li:nth-child(4) > span > button"

        try:
            export_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, export_selector))
            )
            export_button.click()
            print(f"✓ Выбран пункт 'Экспорт' (индекс 4) [{context}]")
            time.sleep(3)
        except Exception as e:
            add_error_with_context(f"Не удалось выбрать 'Экспорт': {e}", context)
            return None

        # 3. Выбираем тип экспорта в зависимости от параметра
        try:
            if export_type == "selected":
                # Для выделенных: #statusChoose > label:nth-child(2)
                selected_selector = "#statusChoose > label:nth-child(2)"
                selected_element = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selected_selector))
                )
                selected_element.click()
                print(f"✓ Выбраны 'Выделенные' [{context}]")
                time.sleep(1)

            elif export_type == "filter":
                # Для фильтра: #statusChoose > label:nth-child(1)
                filter_selector = "#statusChoose > label:nth-child(1)"
                filter_element = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, filter_selector))
                )
                filter_element.click()
                print(f"✓ Выбрано 'По фильтру' [{context}]")
                time.sleep(1)
        except Exception as e:
            add_error_with_context(f"Не удалось выбрать тип экспорта: {e}", context)

        # 4. Получаем количество объектов с фронта в окне экспорта
        counter_selector = "div.flexStart.counterTextModal"
        frontend_count = 0

        try:
            counter_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, counter_selector))
            )
            counter_text = counter_element.text.strip()
            print(f"Текст счетчика: '{counter_text}'")

            # Извлекаем число из текста
            numbers = re.findall(r'\d+', counter_text.replace(',', '').replace(' ', ''))
            if numbers:
                frontend_count = int(numbers[0])
                print(f"✓ Количество записей на фронте для экспорта объектов {export_type}: {frontend_count}")
            else:
                if "Всего 0" in counter_text or "0 записей" in counter_text or counter_text == "0":
                    frontend_count = 0
                    print(f"На фронте 0 записей [{context}]")
        except Exception as e:
            add_error_with_context(f"Не удалось получить количество записей с фронта: {e}", context)

        # 5. Нажимаем кнопку "Выгрузить" (по атрибутам)
        print(f"Нажатие кнопки 'Выгрузить' по атрибутам [{context}]...")

        try:
            # Ждем появления кнопки
            time.sleep(1)

            # Ищем кнопку по атрибутам label и type
            download_button = driver.find_element(By.XPATH, "//button[@label='Выгрузить' and @type='submit']")

            # Прокручиваем к кнопке
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_button)
            time.sleep(0.5)

            # Кликаем через JavaScript
            driver.execute_script("arguments[0].click();", download_button)
            print(f"✓ Кнопка 'Выгрузить' нажата через JavaScript (по атрибутам) [{context}]")
            time.sleep(5)

        except Exception as e:
            add_error_with_context(f"Не удалось нажать кнопку 'Выгрузить' по атрибутам: {e}", context)
            return None

        # 6. Ожидаем загрузку файла
        # Файл называется "Реестр Объектов теплосети от ..."
        latest_file = wait_for_file_download("Реестр*Объектов*теплосети*.xlsx", timeout=45)

        if not latest_file:
            latest_file = wait_for_file_download("Реестр*Объектов*.xlsx", timeout=20)

        if not latest_file:
            latest_file = wait_for_file_download("Объекты*теплосети*.xlsx", timeout=15)

        if not latest_file:
            latest_file = wait_for_file_download("*.xlsx", timeout=15)

        if latest_file:
            print(f"✓ Файл загружен: {os.path.basename(latest_file)} [{context}]")

            # Читаем файл и считаем строки данных
            df = read_excel_file_safe(latest_file)

            # Считаем строки данных (пропускаем заголовки)
            data_rows = 0
            if not df.empty:
                # Обычно в экспорте 2 строки заголовка
                HEADER_ROWS = 2
                if len(df) > HEADER_ROWS:
                    data_rows = len(df) - HEADER_ROWS

            print(f"Файл содержит {data_rows} строк данных (исключая заголовки) [{context}]")

            # Сравниваем
            if data_rows == frontend_count:
                print(f"✓ СОВПАДЕНИЕ: Данные в файле ({data_rows}) совпадают с фронтом ({frontend_count}) [{context}]")
                match_status = "СОВПАДАЕТ"
            else:
                print(
                    f"✗ НЕ СОВПАДЕНИЕ: Данные в файле ({data_rows}) не совпадают с фронтом ({frontend_count}) [{context}]")
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
            add_error_with_context(f"Файл не был загружен", context)
            return None

    except Exception as e:
        add_error_with_context(f"Ошибка при выполнении экспорта объектов {export_type}: {e}", context)
        return None


# ==================== ОСНОВНОЙ КОД ТЕСТА ====================

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

    try:
        wait.until_not(EC.url_contains('login'))
        print("✓ Авторизация успешна")
    except:
        current_url = driver.current_url
        if "login" not in current_url:
            print("✓ Авторизация успешна")
        else:
            raise Exception("Остались на странице логина")

except Exception as e:
    error_msg = f"Авторизация не удалась: {e}"
    add_error_with_context(error_msg, "АВТОРИЗАЦИЯ")
    driver.quit()
    exit()

smart_wait_for_errors_disappear()
wait_for_page_load("После авторизации")

# 2. ПЕРЕХОД В РАЗДЕЛ
print("\n" + "=" * 50)
print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ ОБЪЕКТЫ ТЕПЛОСЕТИ")
print("=" * 50)

section_url = 'http://10.5.121.74/predbilling/accountingObjectsPredBill'
section_name = 'Объекты теплосети'

try:
    driver.get(section_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print(f"✓ Переход в раздел '{section_name}'")
    time.sleep(2)

    smart_wait_for_errors_disappear()
    wait_for_page_load("Переход в объекты теплосети")

except Exception as e:
    error_msg = f"Не удалось перейти в раздел: {e}"
    add_error_with_context(error_msg, "ПЕРЕХОД В РАЗДЕЛ")
    driver.quit()
    exit()

# 3. ПЕРВЫЙ ЭКСПОРТ: ПО ВЫДЕЛЕННЫМ
print("\n" + "=" * 50)
print("ШАГ 3: ЭКСПОРТ ОБЪЕКТОВ ПО ВЫДЕЛЕННЫМ")
print("=" * 50)

# 3.1. Сначала выбираем все объекты через чекбокс
select_all_checkbox_objects("ВЫБОР ВСЕХ ОБЪЕКТОВ")

# 3.2. Выполняем экспорт по выделенным
export_selected_result = perform_export_objects("selected", "ЭКСПОРТ ОБЪЕКТОВ ПО ВЫДЕЛЕННЫМ")
if export_selected_result:
    results_comparison["selected"] = export_selected_result
time.sleep(1)

smart_wait_for_errors_disappear()
close_firefox_download_panel()  # Закрываем панель загрузок как в реестре ведомостей

# Очищаем папку от старых файлов перед следующим экспортом
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
print("ШАГ 4: РАБОТА С ФИЛЬТРОМ ОБЪЕКТОВ")
print("=" * 50)

# 4.1. Открываем фильтр
if open_filter_objects("ОТКРЫТИЕ ФИЛЬТРА"):
    time.sleep(2)
    smart_wait_for_errors_disappear()

    # 4.2. Сбрасываем фильтр перед выбором АО
    reset_filter_objects("СБРОС ФИЛЬТРА")
    time.sleep(1)
    smart_wait_for_errors_disappear()
    wait_for_page_load("После сброса фильтра")

    # 4.3. Выбираем случайное АО
    if select_random_ao_objects("ВЫБОР СЛУЧАЙНОГО АО"):
        print("✓ АО выбрано успешно")
        time.sleep(1)

        # 4.4. Применяем фильтр
        if apply_filter_objects("ПРИМЕНЕНИЕ ФИЛЬТРА"):
            smart_wait_for_errors_disappear()
            wait_for_page_load("После применения фильтра")

            # 5. ЭКСПОРТ ПО ФИЛЬТРУ
            print("\n" + "=" * 50)
            print("ШАГ 5: ЭКСПОРТ ОБЪЕКТОВ ПО ФИЛЬТРУ")
            print("=" * 50)

            # Выполняем экспорт по фильтру (не выделяем чекбоксом!)
            export_filter_result = perform_export_objects("filter", "ЭКСПОРТ ОБЪЕКТОВ ПО ФИЛЬТРУ")
            if export_filter_result:
                results_comparison["filter"] = export_filter_result

            smart_wait_for_errors_disappear()
            close_firefox_download_panel()  # Закрываем панель загрузок как в реестре ведомостей
        else:
            add_error_with_context("Не удалось применить фильтр объектов", "ПРИМЕНЕНИЕ ФИЛЬТРА")
    else:
        add_error_with_context("Не удалось выбрать АО в фильтре объектов", "ВЫБОР АО В ФИЛЬТРЕ")
else:
    add_error_with_context("Не удалось открыть фильтр объектов", "ОТКРЫТИЕ ФИЛЬТРА")

# 6. ИТОГОВЫЙ ОТЧЕТ
print("\n" + "=" * 80)
print("ИТОГОВЫЙ ОТЧЕТ")
print("=" * 80)

print(f"\nРАЗДЕЛ: {section_name}")
print(f"URL: {section_url}")

print(f"\nИТОГ ПРОВЕРКИ ЭКСПОРТА ОБЪЕКТОВ ТЕПЛОСЕТИ:")

test_passed = True

if "selected" in results_comparison:
    result = results_comparison["selected"]
    print(f"\nЭКСПОРТ ОБЪЕКТОВ ПО ВЫДЕЛЕННЫМ:")
    print(f"  Файл: {os.path.basename(result['file'])}")
    print(f"  Строк данных в файле: {result['data_rows']}")
    print(f"  Записей на фронте: {result['frontend_count']}")
    print(f"  Статус: {result['match_status']}")

    if result['match_status'] == "НЕ СОВПАДАЕТ":
        test_passed = False

if "filter" in results_comparison:
    result = results_comparison["filter"]
    print(f"\nЭКСПОРТ ОБЪЕКТОВ ПО ФИЛЬТРУ:")
    print(f"  Файл: {os.path.basename(result['file'])}")
    print(f"  Строк данных в файле: {result['data_rows']}")
    print(f"  Записей на фронте: {result['frontend_count']}")
    print(f"  Статус: {result['match_status']}")

    if result['match_status'] == "НЕ СОВПАДАЕТ":
        test_passed = False

if not results_comparison:
    print("\n⚠ Не удалось выполнить ни одного экспорта объектов")
    test_passed = False

print(f"\nРЕЗУЛЬТАТ ТЕСТА: {'✓ ПРОЙДЕН' if test_passed else '✗ НЕ ПРОЙДЕН'}")

# Выводим ошибки если есть
if section_errors:
    print(f"\nНАЙДЕНО ОШИБОК: {len(section_errors)}")
    print("=" * 60)
    print("СПИСОК ОШИБОК ПО КОНТЕКСТАМ:")

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
    print(f"\n✓ ОШИБОК НЕ НАЙДЕНО")

print(f"\nПАПКА ЗАГРУЗКИ: {DOWNLOAD_FOLDER}")
if os.path.exists(DOWNLOAD_FOLDER):
    files = os.listdir(DOWNLOAD_FOLDER)
    if files:
        print("ЗАГРУЖЕННЫЕ ФАЙЛЫ:")
        for file in files:
            file_path = os.path.join(DOWNLOAD_FOLDER, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"  - {file} ({size:,} байт)")
    else:
        print("Файлы не загружены")

print(f"\n{'=' * 80}")

# 7. ЗАКРЫТИЕ БРАУЗЕРА
try:
    print("\nЗакрытие браузера...")
    time.sleep(2)
    driver.quit()
    print("Браузер успешно закрыт")
except Exception as e:
    print(f"Не удалось закрыть браузер: {e}")