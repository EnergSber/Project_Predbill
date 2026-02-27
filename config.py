import os
from dotenv import load_dotenv
from pathlib import Path

# Загружаем .env файл
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Получаем credentials
USERNAME = os.getenv('UI_USERNAME')
PASSWORD = os.getenv('UI_PASSWORD')

# Проверяем что они есть
if not USERNAME or not PASSWORD:
    raise ValueError("❌  UI_USERNAME и UI_PASSWORD должны быть в .env файле")