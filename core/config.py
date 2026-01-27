import os   #импорт модуля для работы с переменными окружения (ENV)
from dotenv import load_dotenv   #Импорт функции чтобы прочитать файл .env и загрузить переменные из него в окружение (os.environ)

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise Exception('Database url does not exist')
