"""


ЦЕЛЬ: Комплексная проверка работоспособности всех разделов системы Predbilling.

ОПИСАНИЕ ТЕСТА:
1. АВТОРИЗАЦИЯ:
   - Вход в систему с учетными данными
   - Проверка успешного входа по изменению URL и сообщениям

2. ТЕСТИРОВАНИЕ РАЗДЕЛОВ (35 разделов)

ДЛЯ КАЖДОГО РАЗДЕЛА ПРОВЕРЯЕТСЯ:
1. Доступность раздела (переход по URL)
2. Отсутствие ошибок на странице (уведомления, алерты)
3. Работа фильтров (где применимо)
4. Наличие данных в таблицах
5. Умное ожидание исчезновения временных ошибок

ОСОБЕННОСТИ:
- Поддержка 4 типов таблиц: default, komm_tables, analytics_tables, catalog_tables
- Автоматическое ожидание загрузки данных
- Обработка всплывающих сообщений об ошибках/успехе
- Подробный отчет с статистикой и списком ошибок


РЕЗУЛЬТАТ: Детальный отчет о работоспособности всех разделов системы
"""



from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from colorama import init, Fore, Back, Style
init(autoreset=True)

# Креды
URL = 'http://10.5.121.74/login'
USERNAME = 'predbill'
PASSWORD = 'predbill'

# Глобальные селекторы (одинаковые для всех разделов)
FILTER_SELECTOR = "svg[data-icon='filter']"
RESET_SELECTOR = "svg[data-icon='stop']"

# Селекторы таблиц для разных типов разделов
TABLE_SELECTORS = {
    'default': "#root > section > section > main > form > div > div > div > div:nth-child(1) > div > div.BaseTable__table.BaseTable__table-main > div.BaseTable__body",
    'komm_tables': [
        ".BaseTable__body",  # Первый селектор для ИС СБЫТ раздела
        "div.BaseTable__body"  # Второй вариант для надежности ис сбыт
    ],
    'analytics_tables': [  # Новый тип для раздела Аналитика и отчетность
        ".BaseTable__body",  # Таблица со статусами отчетов
        ".ant-table-tbody",  # Таблица с доступными отчетами
        "div.rt-table .BaseTable__body"  # Дополнительный вариант
    ],
    'catalog_tables': [  # Новый тип для раздела Нормативно-Справочная информация
        ".CatalogData",  # Блок с сообщением "Выберите справочник"
        ".catalogList",  # Блок со списком справочников
        ".ant-collapse-item",  # Элементы аккордеона
        ".ant-collapse-header"  # Заголовки аккордеона
    ]
}

# Хранение результатов
all_errors = []
all_results = {}


#Функции
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

#Общее умное ожидание для всех разделов
def smart_wait_for_errors_disappear():
    """Умное ожидание исчезновения ошибок на странице"""
    print("\n⏳ Умное ожидание исчезновения ошибок...")

    def errors_disappeared(driver):
        """Проверяет, что нет видимых ошибок на странице"""
        error_check_selectors = [
            "div.ant-notification-notice-error",
            "div.ant-alert-error",
            ".ant-message-error",
            "div > div > div > div.ant-notification-notice-message",
            "[class*='error']",
            "[class*='danger']",
            ".text-danger",
            ".ant-result-error"
        ]

        for selector in error_check_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    try:
                        if elem.is_displayed():
                            error_text = elem.text.strip()
                            # Если есть текст ошибки и это не положительное сообщение
                            if error_text and len(error_text) > 3:
                                text_lower = error_text.lower()
                                if ("не обнаружено" not in text_lower and
                                        "не найдено" not in text_lower and
                                        "успешно" not in text_lower and
                                        "успешн" not in text_lower and
                                        "завершено" not in text_lower and
                                        "completed" not in text_lower and
                                        "готово" not in text_lower):
                                    return False  # Ошибки еще есть
                    except:
                        continue
            except:
                continue
        return True  # Ошибок нет

    try:
        # Ждем до 60 секунд (используем глобальный wait) пока ошибки не исчезнут
        wait.until(errors_disappeared)
        print("✅ Ошибки исчезли")
        return True
    except Exception as e:
        print(f"⚠ Ошибки не исчезли за время ожидания, продолжаем...")
        return False


#Выполнение теста

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


# Проверка раздела
def test_section(section_url, section_name, check_filters=True, table_type='default'):
    """Проверка раздела с опциональной проверкой фильтров и выбором типа таблицы"""
    print_header(f"ПРОВЕРКА: {section_name}")
    if not check_filters:
        print("⚠ РАЗДЕЛ БЕЗ ПРОВЕРКИ ФИЛЬТРОВ")

    if table_type != 'default':
        print(f"⚠ ТИП ТАБЛИЦЫ: {table_type}")

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
    else:

        # Вызываем умное ожидание для ВСЕХ разделов где найдены ошибки
        smart_wait_for_errors_disappear()

    # Работа с фильтрами (только если check_filters=True)
    if check_filters:
        print("\nРабота с фильтрами:")

        # Открытие фильтра
        if not click_svg_element(FILTER_SELECTOR, "Открыть фильтр"):
            add_error(section_name, "Не удалось открыть фильтр")
            section_errors.append("Ошибка открытия фильтра")

        # Сброс фильтров
        if not click_svg_element(RESET_SELECTOR, "Сбросить фильтры"):
            add_error(section_name, "Не удалось сбросить фильтры")
            section_errors.append("Ошибка сброса фильтров")
    else:
        print("\n⚠ Раздел без фильтров - пропускаем проверку фильтров")

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

        # Выбираем стратегию поиска таблицы в зависимости от типа
        if table_type in ['komm_tables', 'analytics_tables', 'catalog_tables']:
            # Для этих типов ищем все элементы по списку селекторов
            found_elements = []
            element_selectors = TABLE_SELECTORS[table_type]

            for selector in element_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            found_elements.append(element)
                except:
                    continue

            if found_elements:
                print(f"✓ Найдено элементов: {len(found_elements)}")
                total_data_items = 0

                for i, element in enumerate(found_elements, 1):
                    print(f"  Проверка элемента #{i}...")

                    # Определяем тип элемента и адаптируем поиск данных
                    element_text = element.text.strip()
                    element_class = element.get_attribute("class") or ""
                    element_tag = element.tag_name

                    # Проверяем, что это за тип элемента
                    is_table_body = "BaseTable__body" in element_class or "ant-table-tbody" in element_class
                    is_table_row = "BaseTable__row" in element_class or "ant-table-row" in element_class or element_tag == "tr"
                    is_catalog_item = "CatalogData" in element_class or "catalogList" in element_class or "ant-collapse" in element_class

                    if table_type == 'catalog_tables' or is_catalog_item:
                        # Для каталогов проверяем текст самого элемента
                        if element_text and len(element_text) > 5:
                            # Проверяем ключевые элементы каталога
                            if "Выберите справочник" in element_text:
                                print(f"    ✓ Найдено: сообщение выбора справочника")
                            elif "Справочники АСОТ" in element_text:
                                print(f"    ✓ Найдено: раздел 'Справочники АСОТ'")
                            elif "Справочники ЕКС НСИ" in element_text:
                                print(f"    ✓ Найдено: раздел 'Справочники ЕКС НСИ'")
                            else:
                                print(f"    ✓ Текст элемента: '{element_text[:100]}...'" if len(
                                    element_text) > 100 else f"    ✓ Текст элемента: '{element_text}'")
                            total_data_items += 1
                        else:
                            print(f"    ⚠ Элемент #{i} не содержит текста")

                    elif is_table_body:
                        # Для таблиц ищем строки внутри body
                        if table_type == 'analytics_tables':
                            # Для аналитики используем расширенные селекторы
                            rows = element.find_elements(By.CSS_SELECTOR,
                                                         ".BaseTable__row, [role='row'], tr.ant-table-row, tr, .ant-table-row")
                        else:
                            # Для остальных таблиц
                            rows = element.find_elements(By.CSS_SELECTOR,
                                                         ".BaseTable__row, [role='row'], tr")

                        data_rows = []
                        for row in rows:
                            try:
                                row_text = row.text.strip()
                                if row_text and len(row_text) > 10:
                                    data_rows.append(row_text)
                            except:
                                continue

                        if data_rows:
                            print(f"    ✓ Данные в таблице #{i}: {len(data_rows)} строк")
                            total_data_items += len(data_rows)
                            # Показываем пример первой строки
                            if data_rows:
                                sample = data_rows[0]
                                if len(sample) > 100:
                                    print(f"      Пример: {sample[:100]}...")
                                else:
                                    print(f"      Пример: {sample}")
                        else:
                            print(f"    ⚠ Таблица #{i} пуста или строки не найдены")

                    elif is_table_row:
                        # Если нашли сразу строку таблицы
                        if element_text and len(element_text) > 10:
                            print(f"    ✓ Найдена строка: '{element_text[:100]}...'" if len(
                                element_text) > 100 else f"    ✓ Найдена строка: '{element_text}'")
                            total_data_items += 1
                        else:
                            print(f"    ⚠ Строка #{i} не содержит данных")

                    else:
                        # Любой другой элемент
                        if element_text and len(element_text) > 5:
                            print(f"    ✓ Элемент содержит текст: '{element_text[:80]}...'" if len(
                                element_text) > 80 else f"    ✓ Элемент содержит текст: '{element_text}'")
                            total_data_items += 1
                        else:
                            print(f"    ⚠ Элемент #{i} не содержит значимого текста")

                # Проверяем наличие данных для каждого типа
                if total_data_items == 0:
                    if table_type == 'catalog_tables':
                        # Для каталогов проверяем специфические требования
                        all_texts = [elem.text.strip() for elem in found_elements if elem.text.strip()]
                        combined_text = " ".join(all_texts)

                        has_select_message = "Выберите справочник" in combined_text
                        has_catalog_items = "Справочники" in combined_text

                        if not has_select_message or not has_catalog_items:
                            add_error(section_name, "Каталог не содержит необходимых элементов")
                            section_errors.append("Неполный каталог")
                        else:
                            print("✓ Каталог загружен, но не содержит текста в отдельных элементах")
                    else:
                        add_error(section_name, "Нет данных в элементах")
                        section_errors.append("Нет данных")
                else:
                    print(f"✓ Всего найдено данных: {total_data_items}")

                    # Дополнительная проверка для аналитики
                    if table_type == 'analytics_tables' and total_data_items > 0:
                        print("✓ Раздел 'Аналитика и отчетность' содержит данные")

                    # Дополнительная проверка для каталогов
                    if table_type == 'catalog_tables' and total_data_items > 0:
                        all_texts = []
                        for elem in found_elements:
                            if elem.text.strip():
                                all_texts.append(elem.text.strip())

                        combined_text = " ".join(all_texts)
                        has_asot = "Справочники АСОТ" in combined_text
                        has_eks = "Справочники ЕКС НСИ" in combined_text

                        if has_asot and has_eks:
                            print("✓ Найдены оба раздела справочников: АСОТ и ЕКС НСИ")
                        elif has_asot:
                            print("⚠ Найден только раздел: Справочники АСОТ")
                        elif has_eks:
                            print("⚠ Найден только раздел: Справочники ЕКС НСИ")

            else:
                add_error(section_name, "Не найдены элементы")
                section_errors.append("Элементы не найдены")

        else:
            # Стандартный поиск одной таблицы
            table_selector = TABLE_SELECTORS.get(table_type, TABLE_SELECTORS['default'])

            # Проверяем что селектор - это строка (для обычных таблиц)
            if not isinstance(table_selector, str):
                add_error(section_name,
                          f"Неверный тип селектора таблицы: ожидалась строка, получен {type(table_selector)}")
                section_errors.append("Ошибка в селекторе таблицы")
                return section_errors

            table_body = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, table_selector))
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


# Тест разделов
print_header("ТЕСТИРОВАНИЕ РАЗДЕЛОВ")

# Список разделов для проверки (с указанием нужно ли проверять фильтры и тип таблицы)
sections = [
    {
        'url': 'http://10.5.121.74/commercialControl/billingStatements',
        'name': 'Реестр ведомостей',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/commercialControl/watermeterStatements',
        'name': 'Реестр показаний водомеров',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/commercialControl/watermeterStatementUploadLog',
        'name': 'Загрузка файла с данными по ВПУ',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/commercialControl/blocksManagement',
        'name': 'Управление блокировками',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/commercialControl/variableIntervals',
        'name': 'Варьируемые интервалы',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/predbilling/accountingObjectsPredBill',
        'name': 'Объекты теплосети',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/predbilling/commercialNodes',
        'name': 'Узлы учета',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/predbilling/certificates',
        'name': 'Реестр АВЭ|АПП',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/predbilling/meteringDevicesPredBill',
        'name': 'Приборы учета',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/predbilling/simCardsPredBill',
        'name': 'Sim-карты',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/predbilling/transmissionDevicesPredBill',
        'name': 'УСПД',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/predbilling/cabineUspdsPredBill',
        'name': 'Шкаф УСПД',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/technicalControl/meteringPointsPredBill',
        'name': 'Потребление',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/technicalControl/consumptionMvk',
        'name': 'Потребление МВК',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/technicalControl/heatEnergyRelease',
        'name': 'Отпуск тепловой энергии',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/technicalControl/shutdownMeteringPoint',
        'name': 'Отключения',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/technicalControl/weathersPredbill',
        'name': 'Ввод данных с метеостанций',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/technicalControl/modeCardsPredBill',
        'name': 'Режимные карты',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integrations/asupr/statementUploadLog',
        'name': 'АСУПР:Журнал получения ведомостей',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integrations/asupr/directoryReceiptLog',
        'name': 'АСУПР:Журнал получения справочников',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integrations/asupr/comparisonLog',
        'name': 'АСУПР:Журнал сопоставления справочников',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integrations/elk/statementUploadLog',
        'name': 'ЕЛК: Журнал получения ведомостей',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integrations/elk/watermeterStatementUploadLogElk',
        'name': 'ЕЛК: Получение данных из файла по ВПУ',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integration/asot/informationJournal',
        'name': 'АСОТ: Журнал получения данных',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integration/esm/log',
        'name': 'ЕСМ: Журнал взаимодействия',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integration/mvk/log',
        'name': 'МВК: Журнал взаимодействия',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integration/eksnsi/log',
        'name': 'ЕКС НСИ: Журнал обмена данными',
        'check_filters': True,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/integration/komm/logs',
        'name': 'ИС СБЫТ: Журнал обмена данными- Общая статистика',
        'check_filters': False,
        'table_type': 'komm_tables'  # табличное представление для ис сбыт
    },
    {
        'url': 'http://10.5.121.74/integration/komm/errors',
        'name': 'ИС СБЫТ: Журнал обмена данными- Журнал ошибок',
        'check_filters': False,
        'table_type': 'komm_tables'  # табличное представление для ис сбыт
    },
    {
        'url': 'http://10.5.121.74/integrations/application',
        'name': 'Заявки в УКУиКЭ',
        'check_filters': False,
        'table_type': 'default'
    },
    {
        'url': 'http://10.5.121.74/analytics/analyticReportsPredBill',
        'name': 'Аналитика и отчетность',
        'check_filters': False,
        'table_type': 'analytics_tables'
    },
{
        'url': 'http://10.5.121.74/catalog',
        'name': 'Нормативно-справочная информация',
        'check_filters': False,
        'table_type': 'catalog_tables'
    },
{
        'url': 'http://10.5.121.74/administration/roles',
        'name': 'Администрирование:Роли',
        'check_filters': False,
        'table_type': 'default'
    },
{
        'url': 'http://10.5.121.74/administration/systemUsers',
        'name': 'Администрирование:Пользователи',
        'check_filters': False,
        'table_type': 'default'
    },
{
        'url': 'http://10.5.121.74/administration/uiElements',
        'name': 'Администрирование:Элементы интерфейса',
        'check_filters': False,
        'table_type': 'default'
    },
{
        'url': 'http://10.5.121.74/administration/cronRegistry',
        'name': 'Администрирование:Планировщик',
        'check_filters': False,
        'table_type': 'default'
    },


]

# Проверяем все разделы
for section in sections:
    check_filters = section.get('check_filters', True)  # по умолчанию True
    table_type = section.get('table_type', 'default')  # по умолчанию 'default'

    errors = test_section(section['url'], section['name'], check_filters, table_type)

    # Сохраняем результаты
    all_results[section['name']] = {
        'errors': errors,
        'error_count': len(errors),
        'url': section['url'],
        'check_filters': check_filters,
        'table_type': table_type,
        'timestamp': time.strftime('%H:%M:%S')
    }

# Финальный принт
print_header("Финальный принт")

total_errors = len(all_errors)
total_sections = len(all_results)
sections_with_errors = sum(1 for result in all_results.values() if result['error_count'] > 0)
sections_ok = total_sections - sections_with_errors

# Подсчет разделов по типу проверки
sections_with_filters = sum(1 for result in all_results.values() if result.get('check_filters', True))
sections_without_filters = total_sections - sections_with_filters

# Подсчет разделов по типу таблицы
sections_default_table = sum(1 for result in all_results.values() if result.get('table_type', 'default') == 'default')
sections_komm_table = sum(1 for result in all_results.values() if result.get('table_type') == 'komm_tables')

print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
print(f"   • Всего проверено разделов: {total_sections}")
print(f"   • Разделов с проверкой фильтров: {sections_with_filters}")
print(f"   • Разделов без проверки фильтров: {sections_without_filters}")
print(f"   • Разделов со стандартными таблицами: {sections_default_table}")
print(f"   • Разделов с КОММ таблицами: {sections_komm_table}")
print(f"   • Без ошибок: {sections_ok}")
print(f"   • С ошибками: {sections_with_errors}")
print(f"   • Всего ошибок: {total_errors}")

print(f"\n📋 РЕЗУЛЬТАТЫ ПО РАЗДЕЛАМ:")
print(f"{'─' * 60}")

for section_name, result in all_results.items():
    status = "✅ OK" if result['error_count'] == 0 else f"❌ {result['error_count']} ошиб."
    filter_status = "🔍" if result.get('check_filters', True) else "📋"
    table_icon = "📊" if result.get('table_type', 'default') == 'default' else "📈"
    print(f"   • {filter_status}{table_icon} {section_name:32} {status}")

if total_errors > 0:
    print(f"\n⚠ СПИСОК ОШИБОК ({total_errors}):")
    print(f"{'─' * 80}")
    for i, error in enumerate(all_errors, 1):
        print(f"   {i:2}. {error}")

print(f"\n{'═' * 80}")

# Итоговый вывод
if total_errors == 0:
    print(f"{Fore.GREEN}{Style.BRIGHT}🎉 ВСЕ РАЗДЕЛЫ РАБОТАЮТ КОРРЕКТНО!")
    print(f"{Fore.GREEN}✅ Система готова к использованию{Style.RESET_ALL}")
else:
    # КРАСНЫЙ - есть ошибки
    print(f"{Fore.RED}{Style.BRIGHT}🎯 НАЙДЕНО ОШИБОК: {total_errors}")
    print(f"{Fore.RED}⚠ Требуется исправление{Style.RESET_ALL}")


print(f"{'=' * 80}")

# input("\nНажмите Enter для закрытия браузера...")
try:
    print("\nЗакрытие браузера...")
    driver.quit()
    print("✓ Браузер успешно закрыт")
except Exception as e:
    print(f"⚠ Не удалось закрыть браузер: {e}")
    print("⚠ Проверьте, возможно браузер уже закрыт или произошла ошибка")