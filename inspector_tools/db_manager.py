import os
from dotenv import load_dotenv
#loading variables:
load_dotenv()
#reading local variables from .env file
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "backend_lab")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
if __name__ == "__main__":
    print(" Database URL Loaded successfully!")
    print(f"Connecting to DB: {DB_NAME} on {DB_HOST}:{DB_PORT} as {DB_USER}")