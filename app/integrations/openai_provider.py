import os
from pathlib import Path
from configparser import ConfigParser, ExtendedInterpolation

# Tenta importar dependências utilizadas internamente.
# Todas são bibliotecas públicas e independem de acesso via VPN.
try:  # pragma: no cover - podem não estar instaladas
    from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
    from httpx import Client
except Exception:  # pragma: no cover - fora do ambiente interno
    AzureChatOpenAI = None
    AzureOpenAIEmbeddings = None
    Client = None

# Importa classes padrão do LangChain para acesso público.
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

# Constantes com parâmetros usados no ambiente corporativo
_OPENAI_API_VERSION = "2024-03-01-preview"
_OPENAI_BASE_URL = (
    "https://apit.petrobras.com.br/ia/openai/v1/openai-azure/openai/deployments"
)
# Diretório onde ficam os arquivos de configuração fornecidos internamente.
# A busca é feita automaticamente no subdiretório ``app/config``
_CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"

# Caminhos padrão do certificado e da configuração
# Os nomes abaixo não precisam ser configurados manualmente: basta
# colocar ``petrobras-ca-root.pem`` e ``config-v1.x.ini`` dentro de
# ``app/config`` e o módulo fará a leitura automática.
_CERT_PATH = _CONFIG_DIR / "petrobras-ca-root.pem"
_CONFIG_FILE = _CONFIG_DIR / "config-v1.x.ini"


def _load_internal_key() -> str | None:
    """Lê a chave de API do arquivo de configuração interno."""
    # Caso o arquivo não exista, simplesmente retornamos ``None``
    if not _CONFIG_FILE.exists():
        return None

    cfg = ConfigParser(interpolation=ExtendedInterpolation())
    try:
        cfg.read(_CONFIG_FILE, "UTF-8")
        return cfg.get("OPENAI", "OPENAI_API_KEY")
    except Exception:  # pragma: no cover - arquivo opcional
        return None


def _create_azure_chat(model: str):
    """Instancia o cliente AzureChatOpenAI quando possível."""
    if AzureChatOpenAI is None:
        return None
    if not _CERT_PATH.exists():
        # Certificado ausente: não é possível configurar o cliente interno
        return None
    key = _load_internal_key()
    if not key:
        return None
    return AzureChatOpenAI(
        model=model,
        openai_api_version=_OPENAI_API_VERSION,
        openai_api_key=key,
        base_url=f"{_OPENAI_BASE_URL}/{model}",
        http_client=Client(verify=_CERT_PATH),
    )


def _create_azure_embeddings(model: str):
    """Instancia AzureOpenAIEmbeddings quando disponível."""
    if AzureOpenAIEmbeddings is None:
        return None
    if not _CERT_PATH.exists():
        # Certificado ausente: devolve ``None`` para forçar o fallback
        return None
    key = _load_internal_key()
    if not key:
        return None
    return AzureOpenAIEmbeddings(
        model=model,
        openai_api_version=_OPENAI_API_VERSION,
        openai_api_key=key,
        base_url=f"{_OPENAI_BASE_URL}/{model}",
        http_client=Client(verify=_CERT_PATH),
    )


# Indica se devemos usar os serviços internos; controlado por variável de ambiente
def _use_internal_services() -> bool:
    """Retorna ``True`` quando o uso da VPN está habilitado."""
    # Se a variável não estiver definida, assume "1" como padrão
    return os.getenv("VPN_MODE", "1") == "1"


def get_chat_model(model: str = "gpt-3.5-turbo"):
    """Devolve o modelo de chat apropriado ao ambiente."""
    if _use_internal_services():
        chat = _create_azure_chat(model)
        if chat is not None:
            return chat
    # Fallback para API pública
    return ChatOpenAI(model=model)


def get_embeddings(model: str = "text-embedding-ada-002"):
    """Retorna objeto de embeddings adequado ao ambiente."""
    if _use_internal_services():
        emb = _create_azure_embeddings(model)
        if emb is not None:
            return emb
    # Em testes, a classe pode ser substituída por um stub sem parâmetros
    try:
        return OpenAIEmbeddings(model=model)
    except TypeError:  # pragma: no cover - compatibilidade com stubs
        return OpenAIEmbeddings()
