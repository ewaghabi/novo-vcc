import importlib
import types
import os

import pytest

from pathlib import Path

# Ajusta sys.path to import the project root
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Cria stubs leves para as dependências do LangChain
langchain_stub = types.ModuleType("langchain")
langchain_stub.chat_models = types.ModuleType("langchain.chat_models")


class DummyChatOpenAI:
    def __init__(self, *args, **kwargs):
        pass


langchain_stub.chat_models.ChatOpenAI = DummyChatOpenAI
langchain_stub.embeddings = types.ModuleType("langchain.embeddings")


class DummyOpenAIEmbeddings:
    def __init__(self, *args, **kwargs):
        pass


langchain_stub.embeddings.OpenAIEmbeddings = DummyOpenAIEmbeddings
sys.modules.setdefault("langchain", langchain_stub)
sys.modules.setdefault("langchain.chat_models", langchain_stub.chat_models)
sys.modules.setdefault("langchain.embeddings", langchain_stub.embeddings)


class DummyClient:
    def __init__(self, *args, **kwargs):
        pass

import app.integrations.openai_provider as openai_provider


class DummyAzureChat:
    def __init__(self, *args, **kwargs):
        pass


class DummyAzureEmb:
    def __init__(self, *args, **kwargs):
        pass


def reload_provider():
    """Recarrega o módulo para aplicar patches."""
    importlib.reload(openai_provider)


def test_uses_azure_when_available(monkeypatch):
    """Garante uso do Azure quando dependências e chave existem."""
    monkeypatch.setenv("VPN_MODE", "1")
    monkeypatch.setattr(openai_provider, "AzureChatOpenAI", DummyAzureChat)
    monkeypatch.setattr(openai_provider, "AzureOpenAIEmbeddings", DummyAzureEmb)
    monkeypatch.setattr(openai_provider, "Client", DummyClient)
    monkeypatch.setattr(openai_provider, "_load_internal_key", lambda: "k")

    chat = openai_provider.get_chat_model()
    emb = openai_provider.get_embeddings()

    assert isinstance(chat, DummyAzureChat)
    assert isinstance(emb, DummyAzureEmb)


def test_fallback_without_key(monkeypatch):
    """Faz fallback quando não há chave ou dependências."""
    monkeypatch.setenv("VPN_MODE", "1")
    monkeypatch.setattr(openai_provider, "AzureChatOpenAI", DummyAzureChat)
    monkeypatch.setattr(openai_provider, "AzureOpenAIEmbeddings", DummyAzureEmb)
    monkeypatch.setattr(openai_provider, "Client", DummyClient)
    monkeypatch.setattr(openai_provider, "_load_internal_key", lambda: None)

    chat = openai_provider.get_chat_model()
    emb = openai_provider.get_embeddings()

    assert not isinstance(chat, DummyAzureChat)
    assert not isinstance(emb, DummyAzureEmb)


def test_fallback_when_vpn_disabled(monkeypatch):
    """Usa API pública quando VPN_MODE é 0."""
    monkeypatch.setenv("VPN_MODE", "0")
    monkeypatch.setattr(openai_provider, "AzureChatOpenAI", DummyAzureChat)
    monkeypatch.setattr(openai_provider, "AzureOpenAIEmbeddings", DummyAzureEmb)
    monkeypatch.setattr(openai_provider, "Client", DummyClient)
    monkeypatch.setattr(openai_provider, "_load_internal_key", lambda: "k")

    chat = openai_provider.get_chat_model()
    emb = openai_provider.get_embeddings()

    assert not isinstance(chat, DummyAzureChat)
    assert not isinstance(emb, DummyAzureEmb)
