import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME = "RelayWorks AI"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    DATA_DIR = os.getenv("DATA_DIR", "data")


settings = Settings()
