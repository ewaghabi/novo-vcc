import types
import importlib
import sys
from pathlib import Path

# Inclui a raiz do projeto no sys.path para facilitar os imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Função auxiliar para recarregar o módulo de configurações
# Isso garante que as variáveis sejam lidas novamente do ambiente

def reload_settings():
    """Recarrega o módulo de settings com stub de dotenv."""
    sys.modules.pop("app.config.settings", None)
    # Insere módulo fictício para evitar dependência externa
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None
    sys.modules.setdefault("dotenv", dotenv)
    return importlib.import_module("app.config.settings")


def test_default_api_base_url(monkeypatch):
    """Verifica valor padrão quando nenhuma variável é definida."""
    monkeypatch.delenv("API_BASE_URL", raising=False)
    settings = reload_settings()
    assert settings.API_BASE_URL == "http://localhost:8000"


def test_api_base_url_from_env(monkeypatch):
    """Garante que o valor venha da variável de ambiente quando presente."""
    monkeypatch.setenv("API_BASE_URL", "http://exemplo.com")
    settings = reload_settings()
    assert settings.API_BASE_URL == "http://exemplo.com"
