import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

ANS_API_BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/"
ANS_OPERADORAS_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/"

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

REQUEST_TIMEOUT = 60
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "ans_database"),
    "charset": "utf8mb4",
}

CHUNK_SIZE = 10000

CACHE_TTL_SECONDS = 300
