import os
from pathlib import Path

from dotenv import load_dotenv

SRC_DIR = Path(__file__).parent.parent
ENV_FILE = SRC_DIR.parent / ".env"

load_dotenv(ENV_FILE)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

OPENAI_MODEL_NAME = "gpt-4o-mini"
OPENAI_MODEL_TEMPERATURE = 0
OPENAI_EMBEDDINGS_MODEL_NAME = "text-embedding-3-small"

TEXT_SPLITTER_CHUNK_SIZE = 500
TEXT_SPLITTER_CHUNK_OVERLAP = 20

REPORT_FILENAME = "report.csv"
