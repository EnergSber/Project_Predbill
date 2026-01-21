from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time


# ========== КОНФИГУРАЦИЯ ==========
URL = 'http://10.5.121.74/login'
USERNAME = 'predbill'
PASSWORD = 'predbill'

# Глобальные селекторы (одинаковые для всех разделов)
FILTER_SELECTOR = "svg[data-icon='filter']"
RESET_SELECTOR = "svg[data-icon='stop']"
TABLE_SELECTOR = "#root > section > section > main > form > div > div > div > div:nth-child(1) > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body"

# Хранение результатов
all_errors = []
all_results = {}


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def add_error(section_name, error_text):
    """Добавить ошибку"""
    error_msg = f"{section_name}: {error_text}"
    all_errors.append(error_msg)
    print(f"⚠ {error_msg}")


def print_header(text):
    """Печать заголовка"""
    print(f"\n{'=' * 50}")
    print(f" {text}")
    print(f"{'=' * 50}")


def click_svg_element(svg_selector, action_name):
    """Кликнуть на SVG элемент через родительскую кнопку"""
    try:
        # Находим SVG элемент
        svg_element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, svg_selector))
        )
        # Кликаем на родительскую кнопку
        parent_button = svg_element.find_element(By.XPATH, "..")
        parent_button.click()
        print(f"✓ {action_name}")
        time.sleep(1)
        return True
    except Exception as e:
        print(f"✗ Не удалось {action_name}: {e}")
        return False


# ========== ОСНОВНОЙ КОД ==========
print_header("НАЧАЛО ТЕСТИРОВАНИЯ")

# Настройка браузера
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()
wait = WebDriverWait(driver, 60)

# Вход в систему
print_header("АВТОРИЗАЦИЯ")
try:
    driver.get(URL)

    username_field = wait.until(EC.presence_of_element_located((By.ID, "normal_login_username")))
    username_field.send_keys(USERNAME)

    password_field = driver.find_element(By.ID, "normal_login_password")
    password_field.send_keys(PASSWORD)

    driver.find_element(By.CSS_SELECTOR, '.ant-btn.ant-btn-primary.w-100.mb-s').click()

    # Проверка входа - ждем изменения URL
    wait.until_not(EC.url_contains('login'))
    print("✓ Авторизация успешна (URL изменился)")

    # Дополнительная проверка - ищем сообщение об успешном входе
    try:
        success_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div:nth-child(3) > div > div > div > div > div'))
        )
        if "успешный" in success_element.text.lower() or "успешн" in success_element.text.lower():
            print(f"✓ Найдено сообщение: '{success_element.text}'")
        else:
            print(f"⚠ Сообщение найдено, но не об успехе: '{success_element.text}'")
    except:
        print("⚠ Сообщение об успешном входе не найдено")

except Exception as e:
    add_error("Авторизация", f"Ошибка: {str(e)}")
    print("✗ Авторизация не удалась")

    # Проверяем ошибки авторизации если они есть
    try:
        error_elements = driver.find_elements(By.CSS_SELECTOR,
                                              "div.ant-alert-error, .ant-message-error, [class*='error']")
        for error in error_elements:
            if error.is_displayed():
                error_text = error.text.strip()
                if error_text:
                    print(f"⚠ Ошибка авторизации: {error_text}")
                    add_error("Авторизация", error_text)
    except:
        pass


# ========== ФУНКЦИЯ ПРОВЕРКИ РАЗДЕЛА ==========
def test_section(section_url, section_name):
    """Проверка раздела"""
    print_header(f"ПРОВЕРКА: {section_name}")
    section_errors = []

    # Переход в раздел
    try:
        driver.get(section_url)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print(f"✓ Переход в {section_name}")
        time.sleep(2)
    except Exception as e:
        add_error(section_name, f"Не удалось перейти: {e}")
        section_errors.append("Ошибка перехода")
        return section_errors

    # Проверка ошибок на странице
    print("Поиск ошибок на странице...")

    # 1. Проверка по CSS-селекторам
    error_selectors = [
        "div.ant-notification-notice-error",
        "div.ant-alert-error",
        ".ant-message-error",
        "div > div > div > div.ant-notification-notice-message",
        "[class*='error']",
        "[class*='danger']",
        ".text-danger",
        ".ant-result-error"
    ]

    error_found = False
    for selector in error_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                try:
                    if elem.is_displayed():
                        error_text = elem.text.strip()
                        if error_text and error_text not in section_errors:
                            add_error(section_name, error_text)
                            section_errors.append(error_text)
                            error_found = True
                except:
                    continue
        except:
            continue

    # 2. Проверка успешных сообщений (информация)
    try:
        success_elements = driver.find_elements(By.CSS_SELECTOR,
                                                "div.ant-notification-notice-success, div.ant-alert-success, .ant-message-success")
        for elem in success_elements:
            if elem.is_displayed():
                success_text = elem.text.strip()
                if success_text:
                    print(f"  ✓ Успех: {success_text}")
    except:
        pass

    # 3. Поиск слова "ошибка" в уведомлениях и всплывающих сообщениях
    try:
        # Основные места для сообщений об ошибках (в порядке приоритета)
        error_locations = [
            # 1. Уведомления (самый надежный - как в авторизации)
            ("div.ant-notification-notice-message", "уведомление"),

            # 2. Алёрты (красные рамки)
            ("div.ant-alert-error", "алерт"),

            # 3. Всплывающие сообщения
            (".ant-message-error", "сообщение"),

            # 4. Точно такой же селектор как в авторизации для "успешного входа"
            ("body > div:nth-child(3) > div > div > div > div > div", "всплывающее окно"),

            # 5. Модальные окна с ошибками
            ("div.ant-modal-body:has(.ant-alert-error)", "модальное окно"),
        ]

        for selector, location_type in error_locations:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    try:
                        if elem.is_displayed():
                            elem_text = elem.text.strip()
                            if elem_text and len(elem_text) > 3:
                                # Базовые проверки текста
                                text_lower = elem_text.lower()

                                # Ищем индикаторы ошибок
                                has_error = (
                                        "ошибк" in text_lower or
                                        "error" in text_lower or
                                        "не удалось" in text_lower or
                                        "не удалось" in text_lower or
                                        "сбой" in text_lower or
                                        "failure" in text_lower or
                                        "failed" in text_lower
                                )

                                # Исключаем положительные/нейтральные сообщения
                                not_positive = (
                                        "не обнаружено" not in text_lower and
                                        "не найдено" not in text_lower and
                                        "успешно" not in text_lower and
                                        "success" not in text_lower and
                                        "завершено" not in text_lower and
                                        "completed" not in text_lower
                                )

                                if has_error and not_positive:
                                    if elem_text not in section_errors:
                                        print(f"⚠ Найдена ошибка в {location_type}: '{elem_text}'")
                                        add_error(section_name, elem_text)
                                        section_errors.append(elem_text)
                                        error_found = True
                    except:
                        continue
            except:
                continue

    except Exception as e:
        print(f"⚠ Ошибка при поиске текста ошибок: {e}")

    if not error_found:
        print("✓ Явных ошибок не найдено")

    # Работа с фильтрами (только если нет ошибок на странице)
    print("\nРабота с фильтрами:")

    # Если нашли ошибки на странице, ждем пока они исчезнут
    if error_found:
        print("⚠ Найдены ошибки на странице, ждем их исчезновения...")
        try:
            # Ждем исчезновения всех найденных элементов с ошибками
            for selector in error_selectors:
                try:
                    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, selector)))
                except:
                    pass
            print("✓ Ошибки исчезли или таймаут ожидания")
        except:
            print("⚠ Не удалось дождаться исчезновения ошибок")

        # Можно также проверить, нужно ли продолжать тестирование при ошибках
        print("⚠ Продолжаем тестирование несмотря на найденные ошибки...")

    # Открытие фильтра
    if not click_svg_element(FILTER_SELECTOR, "Открыть фильтр"):
        add_error(section_name, "Не удалось открыть фильтр")
        section_errors.append("Ошибка открытия фильтра")

    # Сброс фильтров
    if not click_svg_element(RESET_SELECTOR, "Сбросить фильтры"):
        add_error(section_name, "Не удалось сбросить фильтры")
        section_errors.append("Ошибка сброса фильтров")

    # Проверка данных в таблице
    print("\nПроверка данных в таблице...")
    try:
        # Ждем пока исчезнет надпись "Обновление сопоставленных МВК"
        try:
            wait.until(EC.invisibility_of_element_located((By.XPATH,
                                                           "//*[contains(text(), 'Обновление сопоставленных МВК')]")))
            print("✓ 'Обновление сопоставленных МВК' завершено")
        except:
            print("⚠ Надпись 'Обновление сопоставленных МВК' не найдена или не исчезла")

        # Ждем пока исчезнет надпись "Загрузка..."
        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ant-spin-text")))
            print("✓ Загрузка завершена")
        except:
            print("⚠ Надпись 'Загрузка' не найдена или не исчезла")

        table_body = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, TABLE_SELECTOR))
        )

        # Ищем строки в таблице
        rows = table_body.find_elements(By.CSS_SELECTOR, ".BaseTable__row, tr")
        data_rows = []

        for row in rows:
            try:
                row_text = row.text.strip()
                # Проверяем что строка не пустая и содержит достаточно данных
                if row_text and len(row_text) > 10:
                    data_rows.append(row_text)
            except:
                continue

        if data_rows:
            print(f"✓ Данные в таблице: {len(data_rows)} строк")
            # Показываем пример первой строки
            if data_rows:
                sample = data_rows[0]
                if len(sample) > 100:
                    print(f"  Пример: {sample[:100]}...")
                else:
                    print(f"  Пример: {sample}")
        else:
            add_error(section_name, "Нет данных в таблице")
            section_errors.append("Нет данных в таблице")

    except Exception as e:
        add_error(section_name, f"Ошибка проверки таблицы: {e}")
        section_errors.append("Ошибка проверки таблицы")

    return section_errors


# ========== ТЕСТИРОВАНИЕ РАЗДЕЛОВ ==========
print_header("ТЕСТИРОВАНИЕ РАЗДЕЛОВ")

# Список разделов для проверки
sections = [
    {
        'url': 'http://10.5.121.74/commercialControl/billingStatements',
        'name': 'Реестр ведомостей'
    },
    {
        'url': 'http://10.5.121.74/commercialControl/watermeterStatements',
        'name': 'Реестр показаний водомеров'
    },
{
        'url': 'http://10.5.121.74/commercialControl/watermeterStatementUploadLog',
        'name': 'Загрузка файла с данными по ВПУ'
    },
{
        'url': 'http://10.5.121.74/commercialControl/blocksManagement',
        'name': 'Управление блокировками'
    },
{
        'url': 'http://10.5.121.74/commercialControl/variableIntervals',
        'name': 'Варьируемые интервалы'
    },
{
        'url': 'http://10.5.121.74/predbilling/accountingObjectsPredBill',
        'name': 'Объекты теплосети'
    },
{
        'url': 'http://10.5.121.74/predbilling/commercialNodes',
        'name': 'Узлы учета'
    },
{
        'url': 'http://10.5.121.74/predbilling/certificates',
        'name': 'Реестр АВЭ|АПП'
    },
{
        'url': 'http://10.5.121.74/predbilling/meteringDevicesPredBill',
        'name': 'Приборы учета'
    },
{
        'url': 'http://10.5.121.74/predbilling/simCardsPredBill',
        'name': 'Sim-карты'
    },
{
        'url': 'http://10.5.121.74/predbilling/transmissionDevicesPredBill',
        'name': 'УСПД'
    },
{
        'url': 'http://10.5.121.74/predbilling/cabineUspdsPredBill',
        'name': 'Шкаф УСПД'
    },
{
        'url': 'http://10.5.121.74/technicalControl/meteringPointsPredBill',
        'name': 'Потребление'
    },
{
        'url': 'http://10.5.121.74/technicalControl/consumptionMvk',
        'name': 'Потребление МВК'
    },
{
        'url': 'http://10.5.121.74/technicalControl/heatEnergyRelease',
        'name': 'Отпуск тепловой энергии'
    },
{
        'url': 'http://10.5.121.74/technicalControl/shutdownMeteringPoint',
        'name': 'Отключения'
    },
{
        'url': 'http://10.5.121.74/technicalControl/weathersPredbill',
        'name': 'Ввод данных с метеостанций'
    },
{
        'url': 'http://10.5.121.74/technicalControl/modeCardsPredBill',
        'name': 'Режимные карты'
    },
{
        'url': 'http://10.5.121.74/integrations/asupr/statementUploadLog',
        'name': 'АСУПР:Журнал получения ведомостей'
    },
{
        'url': 'http://10.5.121.74/integrations/asupr/directoryReceiptLog',
        'name': 'АСУПР:Журнал получения справочников'
    },
{
        'url': 'http://10.5.121.74/integrations/asupr/comparisonLog',
        'name': 'АСУПР:Журнал сопоставления справочников '
    },
{
        'url': 'http://10.5.121.74/integrations/asupr/comparisonLog',
        'name': 'АСУПР:Журнал сопоставления справочников '
    },
{
        'url': 'http://10.5.121.74/integrations/elk/statementUploadLog',
        'name': 'ЕЛК: Журнал получения ведомостей '
    },
{
        'url': 'http://10.5.121.74/integrations/elk/statementUploadLog',
        'name': 'ЕЛК: Журнал получения ведомостей '
    },
{
        'url': 'http://10.5.121.74/integrations/elk/watermeterStatementUploadLogElk',
        'name': 'ЕЛК: Получение данных из файла по ВПУ '
    },
{
        'url': 'http://10.5.121.74/integration/asot/informationJournal',
        'name': 'АСОТ: Журнал получения данных '
    },
{
        'url': 'http://10.5.121.74/integration/esm/log',
        'name': 'ЕСМ: Журнал взаимодействия '
    },
{
        'url': 'http://10.5.121.74/integration/mvk/log',
        'name': 'МВК: Журнал взаимодействия '
    },
{
        'url': 'http://10.5.121.74/integration/eksnsi/log',
        'name': 'ЕКС НСИ: Журнал обмена данными '
    },

]

# Проверяем все разделы
for section in sections:
    errors = test_section(section['url'], section['name'])

    # Сохраняем результаты
    all_results[section['name']] = {
        'errors': errors,
        'error_count': len(errors),
        'url': section['url'],
        'timestamp': time.strftime('%H:%M:%S')
    }

# ========== ФИНАЛЬНЫЙ ОТЧЕТ ==========
print_header("ФИНАЛЬНЫЙ ОТЧЕТ")

total_errors = len(all_errors)
total_sections = len(all_results)
sections_with_errors = sum(1 for result in all_results.values() if result['error_count'] > 0)
sections_ok = total_sections - sections_with_errors

print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
print(f"   • Проверено разделов: {total_sections}")
print(f"   • Без ошибок: {sections_ok}")
print(f"   • С ошибками: {sections_with_errors}")
print(f"   • Всего ошибок: {total_errors}")

print(f"\n📋 РЕЗУЛЬТАТЫ ПО РАЗДЕЛАМ:")
print(f"{'─' * 50}")

for section_name, result in all_results.items():
    status = "✅ OK" if result['error_count'] == 0 else f"❌ {result['error_count']} ошиб."
    print(f"   • {section_name:30} {status}")

if total_errors > 0:
    print(f"\n⚠ СПИСОК ОШИБОК ({total_errors}):")
    print(f"{'─' * 70}")
    for i, error in enumerate(all_errors, 1):
        print(f"   {i:2}. {error}")

print(f"\n{'═' * 60}")

# Итоговый вывод
if total_errors == 0:
    print("🎉 ВСЕ РАЗДЕЛЫ РАБОТАЮТ КОРРЕКТНО!")
    print("✅ Система готова к использованию")
else:
    print(f"🎯 НАЙДЕНО ОШИБОК: {total_errors}")
    print(f"⚠ Требуется исправление")

print(f"\n⏱ Время выполнения: {time.strftime('%H:%M:%S')}")
print(f"{'=' * 60}")

#input("\nНажмите Enter для закрытия браузера...")
driver.quit()