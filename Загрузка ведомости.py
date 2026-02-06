import os
import time
import sys
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

if not os.path.exists(FILE_PATH):
    print(f"Создаю файл: {TARGET_FILENAME}")
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.write("<html><body><h1>Тестовый файл для загрузки</h1></body></html>")

print(f"Файл для загрузки: {FILE_PATH}")
print(f"Размер: {os.path.getsize(FILE_PATH)} байт")

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

URL = 'http://10.5.121.74/login'
USERNAME = 'predbill'
PASSWORD = 'predbill'

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

    if file_inputs:
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
                        if (btn.textContent && btn.textContent.includes('Действие')) {
                            return btn;
                        }
                    }
                    return null;
                """)

        if action_button:
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
                        if (btn.textContent && btn.textContent.includes('Загрузка')) {
                            return btn;
                        }
                    }
                    return null;
                """)

        if upload_button:
            upload_button.click()
            print("Кнопка 'Загрузка' нажата")
            time.sleep(2)

            try:
                modal_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
                if modal_inputs:
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

        if not submit_button:
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

        if submit_button:
            break

        time.sleep(1)

    if submit_button:
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

        # Проверяем результат
        try:
            page_source = driver.page_source.lower()
            success_words = ["успешно", "успешн", "загружен", "завершено"]

            for word in success_words:
                if word in page_source:
                    print(f"ЗАГРУЗКА ПРОШЛА УСПЕШНО! (найдено: '{word}')")
                    success = True
                    break
            else:
                print("Сообщение об успехе не найдено")

        except:
            print("Не удалось проверить результат")

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
            if buttons:
                for btn in buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        journal_button = btn
                        print("Кнопка 'Перейти в журнал' найдена по тексту")
                        break
        except:
            pass

        if not journal_button:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, "button.ant-btn.ant-btn-primary.ml-s")
                for btn in buttons:
                    if btn.is_displayed() and "Перейти в журнал" in btn.text:
                        journal_button = btn
                        print("Кнопка найдена по классу ant-btn-primary")
                        break
            except:
                pass

        if not journal_button:
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

        if journal_button:
            break

        time.sleep(1)

    if journal_button:
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

        current_url = driver.current_url
        if "journal" in current_url.lower() or "журнал" in driver.page_source.lower():
            print("Успешный переход в журнал!")
        else:
            print("Переход выполнен, но URL не изменился")

    else:
        print("Кнопка 'Перейти в журнал' не найдена")

except Exception as e:
    print(f"Ошибка при поиске кнопки 'Перейти в журнал': {e}")

print("\n" + "=" * 60)
print("8. ЗАВЕРШЕНИЕ ТЕСТА")
print("=" * 60)

input()
driver.quit()
print("Chrome закрыт")