from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# креды
URL = 'http://10.5.121.74/login'
USERNAME = 'predbill'
PASSWORD = 'predbill'


#  Настройка браузера
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()
wait = WebDriverWait(driver, 40)  # создаем объект ожидания

#  Открытие страницы
driver.get(URL)

#  Ждем появления поля логина и вводим данные
username_field = wait.until(EC.presence_of_element_located((By.ID, "normal_login_username")))
username_field.send_keys(USERNAME)

#  Ввод пароля
password_field = driver.find_element(By.ID, "normal_login_password")
password_field.send_keys(PASSWORD)

#  Нажатие кнопки
driver.find_element(By.CSS_SELECTOR, '.ant-btn.ant-btn-primary.w-100.mb-s').click()

# 5. Проверка входа - ждем изменения URL или появления сообщения
try:
    # Ждем, пока URL перестанет содержать 'login' (редирект после входа)
    wait.until(EC.url_contains('login'))
    print("✗ Ошибка входа (остались на странице логина)")
except:
    print("✓ Вход выполнен (URL изменился)")

#  Ищем надпись "успешный вход"
try:
    success_element = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div:nth-child(3) > div > div > div > div > div'))
    )
    success_text = success_element.text.lower()

    if "успешный" in success_text or "успешн" in success_text:
        print(f"✓ Найдена надпись об успешном входе: '{success_element.text}'")
    else:
        print(f"✗ Надпись найдена, но не содержит 'успешный': '{success_element.text}'")

except:
    print("✗ Надпись 'успешный вход' не найдена")


input("Нажмите Enter для закрытия браузера....")
#driver.quit()