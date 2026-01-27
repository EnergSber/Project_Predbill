import requests
import time
from typing import Dict, Any, Optional


class SystemTester:
    def __init__(self, base_url: str = "http://10.5.121.74"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None

    def make_request(self, name: str, method: str, endpoint: str,
                     data: Optional[Dict] = None, headers: Optional[Dict] = None,
                     expected_status: int = 200) -> bool:
        """
        Универсальный метод для выполнения запросов
        """
        url = f"{self.base_url}{endpoint}"

        try:
            print(f"\n{'=' * 50}")
            print(f"ЗАПРОС: {name}")
            print(f"URL: {url}")
            print(f"МЕТОД: {method}")

            # Добавляем токен к заголовкам если он есть
            request_headers = headers or {}
            if self.token and 'Authorization' not in request_headers:
                request_headers['Authorization'] = f"Bearer {self.token}"

            # Выполняем запрос
            response = self.session.request(
                method=method,
                url=url,
                json=data if data else None,
                headers=request_headers,
                timeout=10
            )

            # Проверяем статус код
            if response.status_code == expected_status:
                print(f"✓ УСПЕХ: Статус {response.status_code}")

                # Если это запрос за токеном, сохраняем его
                if endpoint == "/api/auth/token" and response.status_code == 200:
                    token_data = response.json()
                    self.token = token_data.get('access_token')
                    print(f"Токен получен и сохранен")

                return True
            else:
                print(f"✗ ОШИБКА: Получен статус {response.status_code}, ожидался {expected_status}")
                print(f"Ответ сервера: {response.text[:500]}")  # Ограничиваем вывод
                return False

        except requests.exceptions.Timeout:
            print(f"✗ ТАЙМАУТ: Сервер не ответил за 10 секунд")
            return False
        except requests.exceptions.ConnectionError:
            print(f"✗ ОШИБКА ПОДКЛЮЧЕНИЯ: Не удалось подключиться к серверу")
            return False
        except Exception as e:
            print(f"✗ НЕОЖИДАННАЯ ОШИБКА: {type(e).__name__}: {e}")
            return False

    def test_authentication(self) -> bool:
        """Авторизация"""
        data = {
            "grant_type": "password",
            "username": "predbill",
            "password": "predbill"
        }

        return self.make_request(
            name="АВТОРИЗАЦИЯ",
            method="POST",
            endpoint="/api/auth/token",
            data=data
        )

    def test_main_page(self) -> bool:
        """Тест главной страницы"""
        return self.make_request(
            name="ГЛАВНАЯ СТРАНИЦА",
            method="GET",
            endpoint="/"
        )

    # def test_api_docs(self) -> bool:
    #     """Тест документации API"""
    #     return self.make_request(
    #         name="ДОКУМЕНТАЦИЯ API",
    #         method="GET",
    #         endpoint="/api/docs"
    #     )
    #
    # def test_users_list(self) -> bool:
    #     """Тест получения списка пользователей"""
    #     return self.make_request(
    #         name="СПИСОК ПОЛЬЗОВАТЕЛЕЙ",
    #         method="GET",
    #         endpoint="/api/users"
    #     )
    #
    # def test_reports(self) -> bool:
    #     """Тест получения отчетов"""
    #     return self.make_request(
    #         name="ОТЧЕТЫ",
    #         method="GET",
    #         endpoint="/api/reports"
    #     )
    #
    # def test_settings(self) -> bool:
    #     """Тест настроек"""
    #     return self.make_request(
    #         name="НАСТРОЙКИ",
    #         method="GET",
    #         endpoint="/api/settings"
    #     )
    #
    # def test_statistics(self) -> bool:
    #     """Тест статистики"""
    #     return self.make_request(
    #         name="СТАТИСТИКА",
    #         method="GET",
    #         endpoint="/api/statistics"
    #     )

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("=" * 60)
        print("ЗАПУСК ТЕСТИРОВАНИЯ СИСТЕМЫ")
        print("=" * 60)

        start_time = time.time()
        results = []

        # Запускаем тесты в порядке зависимостей
        tests = [
            ("Авторизация", self.test_authentication),

        ]

        for test_name, test_func in tests:
            print(f"\n>>> Запуск теста: {test_name}")
            result = test_func()
            results.append((test_name, result))
            time.sleep(1)  # Пауза между запросами

        # Вывод итогов
        print("\n" + "=" * 60)
        print("ИТОГИ ТЕСТИРОВАНИЯ:")
        print("=" * 60)

        successful = 0
        failed = 0

        for test_name, result in results:
            status = "✓ УСПЕХ" if result else "✗ ОШИБКА"
            print(f"{status}: {test_name}")
            if result:
                successful += 1
            else:
                failed += 1

        print("\n" + "=" * 60)
        print(f"УСПЕШНЫХ: {successful}")
        print(f"ПРОВАЛЕННЫХ: {failed}")
        print(f"ОБЩЕЕ ВРЕМЯ: {time.time() - start_time:.2f} секунд")

        if failed == 0:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print("⚠ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
        print("=" * 60)


# Пример использования
if __name__ == "__main__":
    # Создаем тестер
    tester = SystemTester(base_url="http://10.5.121.74")

    # Запускаем все тесты
    tester.run_all_tests()