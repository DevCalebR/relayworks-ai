import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME = "RelayWorks AI"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


settings = Settings()
