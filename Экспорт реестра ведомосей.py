'''ТЕСТ: Экспорт реестра ведомостей в Excel через веб-интерфейс "Предбиллинг"

Что тестирует:
1. Авторизация в системе
2. Переход в раздел "Реестр ведомостей"
3. Экспорт всех ведомостей (по выделенным)
4. Работа с фильтром:
   - Очистка полей периода
   - Выбор случайного АО
   - Применение фильтра
5. Экспорт отфильтрованных ведомостей (по фильтру)
6. Сравнение количества записей в файле Excel с количеством на фронтенде


Ключевые проверки:
- Корректность авторизации
- Доступность раздела
- Работоспособность фильтрации
- Корректность экспорта в XLSX
- Соответствие данных в файле данным на фронтенде
- Обработка ошибок и уведомлений

Результат: итоговый отчет с количеством ошибок и статусом теста'''





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

print("=" * 60)
print("ТЕСТ РАЗДЕЛА: Экспорт ведомостей в Excel")
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
URL = 'http://10.5.121.74/login'
USERNAME = 'predbill'
PASSWORD = 'predbill'

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
                                # Пробуем обычный клик
                                try:
                                    btn.click()
                                except:
                                    # Если не получается, пробуем через JavaScript
                                    driver.execute_script("arguments[0].click();", btn)

                                print(f"Найден и кликнут крестик")
                                time.sleep(0.2)
                                return True
                        except:
                            # Пробуем клик через JavaScript даже если элемент не видим
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
        # Ждем до 15 секунд пока ошибки не исчезнут
        while time.time() - start_wait_time < max_wait_time:
            # Проверяем, есть ли ошибки сейчас
            if check_for_persistent_errors():
                elapsed = time.time() - start_wait_time

                # Если ошибка держится больше 0.5 секунды, пытаемся закрыть
                if elapsed > 0.5:
                    print(f"Ошибка держится {elapsed:.1f}с, пробуем закрыть...")
                    if try_close_error():
                        print(f"Попытка закрытия выполнена")
                        time.sleep(0.5)
                    else:
                        print(f"Не удалось найти кнопку закрытия")

                time.sleep(0.5)
            else:
                # Ошибок нет
                print(f"Ошибки исчезли")
                return True

        # Если вышли по таймауту
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
        # Список CSS-селекторов для поиска элементов загрузки
        loading_selectors = [
            "div.ant-spin.ant-spin-spinning",
            "div.ant-spin-spinning",
            "div.ant-spin-text",
            "span.anticon-loading.anticon-spin",
            "span.ant-spin-dot",
            "div.ant-spin-container"
        ]

        # Проверяем каждый селектор
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
    """Закрывает панель загрузок Firefox через JavaScript"""
    try:
        print("Закрытие панели загрузок Firefox...")

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


def wait_for_file_download(filename_pattern="Реестр*ведомостей*.xlsx", timeout=60):
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
                    # Читаем без заголовков
                    df = pd.read_excel(file_path, engine=engine, header=None)
                elif file_ext == '.xls':
                    df = pd.read_excel(file_path, engine=engine, header=None)
                else:
                    df = pd.read_excel(file_path, engine=engine, header=None)

                if df is not None:
                    return df

            except:
                continue

        return pd.DataFrame()  # Возвращаем пустой DataFrame если не удалось прочитать

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


def clear_date_period_fields(context=""):
    """Быстрая очистка полей периода через JavaScript"""
    try:
        print(f"Очистка полей периода [{context}]...")

        js_code = """
        var startInput = document.querySelector('#startMonth');
        if (startInput) {
            startInput.value = '';
            var inputEvent = new Event('input', { bubbles: true });
            var changeEvent = new Event('change', { bubbles: true });
            startInput.dispatchEvent(inputEvent);
            startInput.dispatchEvent(changeEvent);
        }

        var endInput = document.querySelector('#finishMonth');
        if (endInput) {
            endInput.value = '';
            endInput.dispatchEvent(new Event('input', { bubbles: true }));
            endInput.dispatchEvent(new Event('change', { bubbles: true }));
        }

        var clearButtons = document.querySelectorAll('.ant-picker-clear');
        clearButtons.forEach(function(btn) {
            if (btn.offsetParent !== null && btn.style.display !== 'none') {
                btn.click();
            }
        });

        return 'Очищено';
        """

        result = driver.execute_script(js_code)
        print(f"Поля периода очищены [{context}]")
        time.sleep(0.5)

        return True

    except Exception as e:
        error_msg = f"Ошибка при очистке полей периода: {e}"
        add_error_with_context(error_msg, context)
        return False


def click_reset_button(context=""):
    """Нажимает кнопку сброса (иконка stop)"""
    try:
        print(f"Нажатие кнопки сброса [{context}]...")

        # Ищем кнопку сброса по нескольким селекторам
        reset_selectors = [
            "svg[data-icon='stop']",  # По иконке
            ".anticon-stop",  # По классу иконки
            "button[type='button'] .anticon-stop",  # Кнопка с иконкой stop
            "button.ant-btn-icon-only .anticon-stop"  # Кнопка только с иконкой
        ]

        for selector in reset_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        # Если нашли иконку, ищем родительскую кнопку
                        if element.tag_name.lower() == 'svg' or 'anticon-stop' in element.get_attribute("class", ""):
                            try:
                                button = element.find_element(By.XPATH, "./ancestor::button")
                                if button and button.is_displayed() and button.is_enabled():
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                                    time.sleep(0.3)
                                    button.click()
                                    print(f"Кнопка сброса нажата [{context}]")
                                    time.sleep(1)
                                    return True
                            except:
                                # Если не нашли родительскую кнопку, кликаем на сам элемент
                                if element.is_displayed() and element.is_enabled():
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                    time.sleep(0.3)
                                    element.click()
                                    print(f"Кнопка сброса нажата (через иконку) [{context}]")
                                    time.sleep(1)
                                    return True
                    except:
                        continue
            except:
                continue

        # Пробуем найти через JavaScript
        try:
            reset_button = driver.execute_script("""
                var buttons = document.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    if (btn.querySelector('svg[data-icon="stop"]') || 
                        btn.querySelector('.anticon-stop')) {
                        return btn;
                    }
                }
                return null;
            """)

            if reset_button:
                driver.execute_script("arguments[0].click();", reset_button)
                print(f"Кнопка сброса нажата через JavaScript [{context}]")
                time.sleep(1)
                return True
        except:
            pass

        print(f"Кнопка сброса не найдена [{context}]")
        return False

    except Exception as e:
        error_msg = f"Ошибка при нажатии кнопки сброса: {e}"
        add_error_with_context(error_msg, context)
        return False


def select_random_ao(context=""):
    """Выбирает случайное АО в фильтре"""
    try:
        print(f"Выбор случайного АО в фильтре [{context}]...")

        # Ищем поле АО
        ao_selectors = [
            "input#aoCode[type='search']",
            "#aoCode",
            "input.ant-select-selection-search-input",
            "div[class*='ant-select-in-form-item'] input",
            "div.ant-select-selector input",
            ".ant-select-selector",
        ]

        ao_field = None
        for selector in ao_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        element_id = element.get_attribute("id") or ""
                        element_class = element.get_attribute("class") or ""
                        if ("aoCode" in element_id or "ant-select-selection-search-input" in element_class):
                            ao_field = element
                            print(f"Найдено поле АО: {selector}")
                            break
                    except:
                        continue
                if ao_field:
                    break
            except:
                continue

        if not ao_field:
            try:
                ao_field = driver.find_element(By.XPATH, "//input[@id='aoCode']")
                print(f"Найдено поле АО по XPath")
            except:
                error_msg = "Поле АО не найдено"
                add_error_with_context(error_msg, context)
                return False

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ao_field)
        time.sleep(0.5)

        try:
            ao_field.click()
            print(f"Кликнули на поле АО")
            time.sleep(1)
        except:
            try:
                parent_div = ao_field.find_element(By.XPATH, "./ancestor::div[contains(@class, 'ant-select-selector')]")
                parent_div.click()
                print(f"Кликнули на родительский div поля АО")
                time.sleep(1)
            except Exception as e2:
                error_msg = f"Не удалось кликнуть на поле АО: {e2}"
                add_error_with_context(error_msg, context)
                return False

        print(f"Ожидание появления списка АО...")
        time.sleep(1.5)

        # Ищем опции АО
        options = []
        option_selectors = [
            "div.ant-select-item-option[title]",
            "div[aria-label]",
            "div.ant-select-item-option .ant-select-item-option-content",
            "div[role='option']",
        ]

        for selector in option_selectors:
            try:
                found_options = driver.find_elements(By.CSS_SELECTOR, selector)
                for option in found_options:
                    try:
                        option_text = option.text.strip()
                        if option_text and "Выбрать все" not in option_text:
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
                                                     "not(contains(text(), 'Выбрать все'))]"
                                                     )

                for option in xpath_options:
                    try:
                        option_text = option.text.strip()
                        if option_text and option_text not in ["Выбрать все", "Select all"]:
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
                print(f"Выбрано случайное АО: '{option_text}'")
                time.sleep(1)
                return True
            except:
                try:
                    driver.execute_script("arguments[0].click();", random_option)
                    print(f"Выбрано случайное АО через JS: '{option_text}'")
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


def apply_filter(context=""):
    """Нажимает кнопку Применить в фильтре"""
    try:
        print(f"Применение фильтра [{context}]...")

        # Сначала пробуем найти по тексту
        try:
            button = driver.find_element(By.XPATH, "//button[contains(., 'Применить')]")
            print(f"Найдена кнопка 'Применить' по тексту")
            button.click()
            print(f"Фильтр применен [{context}]")
            time.sleep(3)
            return True
        except:
            pass

        # Ищем по иконке check
        apply_selectors = [
            "button:has(svg[data-icon='check'])",
            "button.ant-btn-primary",
            "svg[data-icon='check']",
            ".anticon-check",
            "div.filterOperations > button:nth-child(1)",
            "div.filterOperations button",
        ]

        for selector in apply_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        tag_name = element.tag_name.lower()
                        if tag_name == 'button':
                            if element.is_displayed() and element.is_enabled():
                                element.click()
                                print(f"Найдена и нажата кнопка: {selector}")
                                print(f"Фильтр применен [{context}]")
                                time.sleep(3)
                                return True
                        elif tag_name in ['span', 'svg']:
                            try:
                                button = element.find_element(By.XPATH, "./ancestor::button")
                                if button and button.is_displayed() and button.is_enabled():
                                    button.click()
                                    print(f"Найдена кнопка через иконку: {selector}")
                                    print(f"Фильтр применен [{context}]")
                                    time.sleep(3)
                                    return True
                            except:
                                pass
                    except:
                        continue
            except:
                continue

        # Пробуем через JavaScript
        try:
            button = driver.execute_script("""
                var buttons = document.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    if (btn.querySelector('svg[data-icon="check"]') || 
                        btn.querySelector('.anticon-check') ||
                        btn.textContent.includes('Применить')) {
                        return btn;
                    }
                }
                return null;
            """)

            if button:
                driver.execute_script("arguments[0].click();", button)
                print(f"Фильтр применен через JavaScript [{context}]")
                time.sleep(3)
                return True
        except:
            pass

        error_msg = "Не удалось найти кнопку 'Применить'"
        add_error_with_context(error_msg, context)
        return False

    except Exception as e:
        error_msg = f"Ошибка при применении фильтра: {str(e)[:150]}"
        add_error_with_context(error_msg, context)
        return False


def get_export_frontend_records_count(context=""):
    """Получает количество записей с фронта в окне экспорта с дополнительными ожиданиями"""
    try:
        print(f"Получение количества записей с фронта в окне экспорта [{context}]...")


        time.sleep(2)

        # Пробуем несколько селекторов для счетчика
        counter_selectors = [
            "div.flexStart.counterTextModal",
            ".counterTextModal",
            "body > div:nth-child(6) > div > div.ant-modal-wrap.ant-modal-centered > div > div.ant-modal-content > div > form > div.rt-form-body.rt-form-body-no-padding > div > div.flexStart.flexColumn > div.flexStart.counterTextModal"
        ]

        counter_element = None
        for selector in counter_selectors:
            try:
                counter_element = driver.find_element(By.CSS_SELECTOR, selector)
                if counter_element and counter_element.is_displayed():
                    print(f"Счетчик найден по селектору: {selector}")
                    break
            except:
                continue

        if not counter_element:
            # Пробуем найти через XPath
            try:
                counter_element = driver.find_element(By.XPATH, "//div[contains(@class, 'counterTextModal')]")
                print(f"Счетчик найден по XPath")
            except:
                error_msg = "Не удалось найти элемент счетчика в окне экспорта"
                add_error_with_context(error_msg, context)
                return 0

        # Ждем обновления текста счетчика
        max_attempts = 10
        last_text = ""

        for attempt in range(max_attempts):
            try:
                current_text = counter_element.text.strip()

                if current_text and current_text != last_text:
                    print(f"Текст счетчика (попытка {attempt + 1}): '{current_text}'")
                    last_text = current_text

                    # Проверяем, не содержит ли текст "Загрузка" или спиннер
                    if "Загрузка" not in current_text and "loading" not in current_text.lower():
                        # Извлекаем число из текста
                        numbers = re.findall(r'\d+', current_text.replace(',', '').replace(' ', ''))
                        if numbers:
                            count = int(numbers[0])
                            print(f"Извлечено число: {count} [{context}]")
                            return count
                        else:
                            # Проверяем специальные случаи
                            if "Всего 0" in current_text or "0 записей" in current_text or current_text == "0":
                                print(f"На фронте 0 записей [{context}]")
                                return 0

                time.sleep(1)
            except:
                time.sleep(1)
                continue

        print(f"Не удалось получить актуальный текст счетчика за {max_attempts} попыток [{context}]")
        return 0

    except Exception as e:
        print(f"Ошибка при получении количества записей с фронта: {e} [{context}]")
        return 0


def count_data_rows_in_excel(df):
    """Считает только строки с данными, пропуская первые 2 строки заголовка"""
    if df.empty:
        return 0

    # Для данного экспорта всегда пропускаем первые 2 строки как заголовок
    HEADER_ROWS = 2

    if len(df) <= HEADER_ROWS:
        return 0

    # Считаем строки с данными после заголовков
    data_rows = 0
    for idx in range(HEADER_ROWS, len(df)):
        row = df.iloc[idx]
        row_has_data = False

        # Проверяем каждую ячейку в строке на наличие данных
        for cell in row:
            if pd.notna(cell):
                cell_str = str(cell).strip()
                # Игнорируем пустые значения
                if cell_str and cell_str not in ['', 'nan', 'NaN', 'None']:
                    # Проверяем, что это не пустая строка и не заголовок
                    if len(cell_str) > 0:
                        row_has_data = True
                        break

        if row_has_data:
            data_rows += 1

    print(f"Всего строк в файле: {len(df)}, строк заголовка: {HEADER_ROWS}, строк данных: {data_rows}")
    return data_rows


def perform_export(export_type="selected", context=""):
    """Выполняет экспорт данных и сравнивает внутри себя"""
    try:
        print(f"Выполнение экспорта: {export_type} [{context}]")

        # 1. Открываем меню "Действие"
        action_button_selector = "#root > section > section > div > div.ant-space.ant-space-horizontal.ant-space-align-center > div > div > div > div > div > button > div > div:nth-child(1) > span > svg"

        if not click_svg_element(action_button_selector, "Открыть меню 'Действие'", context):
            add_error_with_context(f"Не удалось открыть меню 'Действие' для экспорта {export_type}", context)
            return None

        print(f"Меню 'Действие' открыто [{context}]")
        time.sleep(2)

        # 2. Выбираем "Экспорт"
        export_selector = "html > div > div > div > ul > li:nth-child(2) > span > button"

        try:
            export_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, export_selector))
            )
            export_button.click()
            print(f"Выбран пункт 'Экспорт' [{context}]")
            time.sleep(3)
        except Exception as e:
            add_error_with_context(f"Не удалось выбрать 'Экспорт': {e}", context)
            return None

        # 3. Переходим на вкладку "Экспорт реестра"
        tab_selector = "#tabView-tab-report"

        try:
            tab_element = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, tab_selector))
            )
            tab_element.click()
            print(f"Перешли на вкладку 'Экспорт реестра' [{context}]")
            time.sleep(2)
        except Exception as e:
            add_error_with_context(f"Не удалось перейти на вкладку: {e}", context)
            return None

        # 4. Выбираем формат XLS
        time.sleep(2)
        try:
            xls_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'xlsXLS', 'XLSXLS'), 'XLS')]")
            for element in xls_elements:
                try:
                    element_text = element.text.strip()
                    if "XLS" in element_text.upper() and len(element_text) < 10:
                        element.click()
                        print(f"Выбран формат: {element_text} [{context}]")
                        break
                except:
                    continue
        except:
            pass

        # 5. Выбираем тип экспорта
        try:
            if export_type == "selected":
                selected_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Выделенные')]")
                for element in selected_elements:
                    try:
                        element_text = element.text.strip()
                        if "Выделенные" in element_text:
                            element_class = element.get_attribute("class")
                            if "ant-radio-button-checked" not in element_class:
                                element.click()
                                print(f"Выбраны 'Выделенные' [{context}]")
                                time.sleep(1)
                            break
                    except:
                        continue

            elif export_type == "filter":
                filter_selectors = [
                    "#formatChoose > label:nth-child(1)",
                    "//span[contains(text(), 'По фильтру')]",
                    "#formatChoose > label:nth-child(1) > span:nth-child(2)"
                ]

                for selector in filter_selectors:
                    try:
                        if selector.startswith("//"):
                            element = driver.find_element(By.XPATH, selector)
                        else:
                            element = driver.find_element(By.CSS_SELECTOR, selector)

                        if element:
                            element_class = element.get_attribute("class")
                            if "ant-radio-button-checked" not in element_class:
                                element.click()
                                print(f"Выбрано 'По фильтру' [{context}]")
                                time.sleep(1)
                                break
                    except:
                        continue
        except:
            pass

        # 6. Получаем количество ведомостей с фронта в окне экспорта
        frontend_count = get_export_frontend_records_count(f"Экспорт {export_type}")

        print(f"Количество записей на фронте для экспорта {export_type}: {frontend_count}")

        # 7. Нажимаем кнопку "Выгрузить"
        try:
            download_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Выгрузить')]"))
            )
            download_button.click()
            print(f"Кнопка 'Выгрузить' нажата [{context}]")
            time.sleep(5)
        except Exception as e:
            add_error_with_context(f"Не удалось нажать кнопку 'Выгрузить': {e}", context)
            return None

        # 8. Ожидаем загрузку файла
        latest_file = wait_for_file_download("Реестр*ведомостей*.xlsx", timeout=45)

        if not latest_file:
            latest_file = wait_for_file_download("Реестр*.xlsx", timeout=20)

        if not latest_file:
            latest_file = wait_for_file_download("*.xlsx", timeout=15)

        if latest_file:
            print(f"Файл загружен: {os.path.basename(latest_file)} [{context}]")

            # Читаем файл БЕЗ заголовков
            df = read_excel_file_safe(latest_file)

            # Считаем только строки с данными, игнорируя заголовки
            data_rows = count_data_rows_in_excel(df)

            print(f"Файл содержит {data_rows} строк данных (исключая заголовки) [{context}]")

            # Сравниваем внутри экспорта
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
        add_error_with_context(f"Ошибка при выполнении экспорта {export_type}: {e}", context)
        return None


# Основной код теста

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
        print("Авторизация успешна")
    except:
        current_url = driver.current_url
        if "login" not in current_url:
            print("Авторизация успешна")
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
print("ШАГ 2: ПЕРЕХОД В РАЗДЕЛ РЕЕСТР ВЕДОМОСТЕЙ")
print("=" * 50)

section_url = 'http://10.5.121.74/commercialControl/billingStatements'
section_name = 'Реестр ведомостей'

try:
    driver.get(section_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print(f"Переход в раздел '{section_name}'")
    time.sleep(2)

    smart_wait_for_errors_disappear()
    wait_for_page_load("Переход в реестр ведомостей")

except Exception as e:
    error_msg = f"Не удалось перейти в раздел: {e}"
    add_error_with_context(error_msg, "ПЕРЕХОД В РАЗДЕЛ")
    driver.quit()
    exit()

# 3. ПЕРВЫЙ ЭКСПОРТ: ПО ВЫДЕЛЕННЫМ
print("\n" + "=" * 50)
print("ШАГ 3: ЭКСПОРТ ПО ВЫДЕЛЕННЫМ")
print("=" * 50)

print("Выбор всех ведомостей через чекбокс...")
checkbox_selector = "#root > section > section > main > form > div > div > div > div > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__header > div > div > div:nth-child(1) > label"

try:
    checkbox = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, checkbox_selector))
    )
    checkbox.click()
    print("Выбраны все ведомости через чекбокс")
    time.sleep(2)
    smart_wait_for_errors_disappear()
except Exception as e:
    error_msg = f"Не удалось выбрать все ведомости: {e}"
    add_error_with_context(error_msg, "ВЫБОР ВСЕХ ВЕДОМОСТЕЙ")

export_selected_result = perform_export("selected", "ЭКСПОРТ ПО ВЫДЕЛЕННЫМ")
if export_selected_result:
    results_comparison["selected"] = export_selected_result
time.sleep(1)

smart_wait_for_errors_disappear()
close_firefox_download_panel()

# Очищаем папку от старых файлов
if os.path.exists(DOWNLOAD_FOLDER):
    print(f"\nОчистка папки: {DOWNLOAD_FOLDER}")
    for file in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, file)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                print(f"Удален старый файл: {file}")
            except:
                pass

# 4. РАБОТА С ФИЛЬТРОМ
print("\n" + "=" * 50)
print("ШАГ 4: РАБОТА С ФИЛЬТРОМ")
print("=" * 50)

print("Открытие фильтра...")
filter_selector = "svg[data-icon='filter']"
if click_svg_element(filter_selector, "Открыть фильтр", "ОТКРЫТИЕ ФИЛЬТРА"):
    print("Фильтр открыт")
    time.sleep(2)
    smart_wait_for_errors_disappear()
else:
    add_error_with_context("Не удалось открыть фильтр", "ОТКРЫТИЕ ФИЛЬТРА")

# 4.1. Очищаем поля периода
clear_date_period_fields("ОЧИСТКА ПОЛЕЙ ПЕРИОДА")

# 4.2. Нажимаем кнопку сброса (перед выбором АО)
click_reset_button("СБРОС ФИЛЬТРА ПЕРЕД ВЫБОРОМ АО")

# Проверяем ошибки после сброса
smart_wait_for_errors_disappear()
time.sleep(1)

# 4.3. Выбираем случайное АО
if select_random_ao("ВЫБОР СЛУЧАЙНОГО АО"):
    print("АО выбрано успешно")

    # 4.4. Применяем фильтр
    if apply_filter("ПРИМЕНЕНИЕ ФИЛЬТРА"):
        print("Фильтр применен успешно")
        smart_wait_for_errors_disappear()
        wait_for_page_load("После применения фильтра")

        # 4.5. Выполняем экспорт по фильтру
        print("\n" + "=" * 50)
        print("ШАГ 5: ЭКСПОРТ ПО ФИЛЬТРУ")
        print("=" * 50)

        export_filter_result = perform_export("filter", "ЭКСПОРТ ПО ФИЛЬТРУ")
        if export_filter_result:
            results_comparison["filter"] = export_filter_result

        smart_wait_for_errors_disappear()
    else:
        add_error_with_context("Не удалось применить фильтр", "ПРИМЕНЕНИЕ ФИЛЬТРА")
else:
    add_error_with_context("Не удалось выбрать АО в фильтре", "ВЫБОР АО В ФИЛЬТРЕ")

# 6. ИТОГОВЫЙ ОТЧЕТ
print("\n" + "=" * 80)
print("ИТОГОВЫЙ ОТЧЕТ")
print("=" * 80)

print(f"\nРАЗДЕЛ: {section_name}")
print(f"URL: {section_url}")

print(f"\nИТОГ ПРОВЕРКИ ЭКСПОРТА:")

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
    print("\nНе удалось выполнить ни одного экспорта")
    test_passed = False

print(f"\nРЕЗУЛЬТАТ ТЕСТА: {'ПРОЙДЕН' if test_passed else 'НЕ ПРОЙДЕН'}")

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
    print(f"\nОШИБОК НЕ НАЙДЕНО")

#print(f"\nПАПКА ЗАГРУЗКИ: {DOWNLOAD_FOLDER}")
if os.path.exists(DOWNLOAD_FOLDER):
    files = os.listdir(DOWNLOAD_FOLDER)
    if files:
        #print("ЗАГРУЖЕННЫЕ ФАЙЛЫ:")
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