import os

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "streaming")
DB_USER = os.environ.get("DB_USER", "streaming")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "streaming")
POOL_SIZE = int(os.environ.get("POOL_SIZE", "16"))
PORT = int(os.environ.get("PORT", "8080"))
WORKERS = int(os.environ.get("WORKERS", "2"))

TAMANHO_PADRAO = 20
TAMANHO_MAXIMO = 200