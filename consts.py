import os
from dotenv import load_dotenv
from datetime import time

load_dotenv()


TOKEN = os.getenv("TOKEN", "no token set")
OWNER_ID = int(os.getenv("OWNER_ID", "-1"))
QUIZ_CHANNEL_ID = int(os.getenv("QUIZ_CHANNEL_ID", "-1"))
TABLE_CHANNEL_ID = int(os.getenv("TABLE_CHANNEL_ID", "-1"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "-1"))
QUIZ_FOLDER = f"resources/{os.getenv('QUIZ_FOLDER', '')}"
QUIZ_TIME = time(0, 0, 0)
REMINDER_TIME = time(15, 0, 0)
