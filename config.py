import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_BASE_URL = "https://api.gptnix.online/v1"
API_KEY = os.getenv("API_KEY", "sk-av-v1-noq_Ig2pG6epdhC880sybnd4Sb_j2zs4ZiZUj5tDK05HqhLgy7GcwwGrnyloFufcEuf7_8jMcQRP2RsWIwXBk4Gwmdw2IU5jvKPWRQ58cO7sUlZSsfWBKAj")
DEFAULT_MODEL = "google/gemini-2.5-flash"
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
