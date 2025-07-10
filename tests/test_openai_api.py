import os
import pytest

import openai

# Testa conexão com o endpoint de chat/completion da OpenAI
@pytest.mark.skipif('OPENAI_API_KEY' not in os.environ, reason='requere chave da API')
def test_openai_chat_completion():
    """Verifica se o modelo de chat responde"""
    resp = openai.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'user', 'content': 'Olá'}],
    )
    assert resp and resp.choices

# Testa criação de embeddings com o modelo adequado
@pytest.mark.skipif('OPENAI_API_KEY' not in os.environ, reason='requere chave da API')
def test_openai_embeddings():
    """Garante que o endpoint de embeddings está acessível"""
    resp = openai.embeddings.create(
        model='text-embedding-ada-002',
        input='teste',
    )
    assert resp and resp.data
