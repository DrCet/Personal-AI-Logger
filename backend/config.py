import urllib.parse
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

username = "cet"
password = "your_password"
host = "localhost"
port = "5432"
database = "personal_ai_logger"

encoded_password = urllib.parse.quote(password)  # Encodes @ as %40
DATABASE_URL = f"postgresql+asyncpg://{username}:{encoded_password}@{host}:{port}/{database}"
print(f"Generated DATABASE_URL: {DATABASE_URL}")