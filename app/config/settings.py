import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env

load_dotenv()

# Endereço base da API utilizado pelo frontend
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
