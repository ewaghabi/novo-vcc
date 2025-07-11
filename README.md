# Novo Verificador de Cláusulas Contratuais (VCC) – Sistema de Análise e Consulta de Contratos com LLM

Este projeto é uma plataforma em Python que utiliza modelos de linguagem (LLMs), busca vetorial e uma interface interativa para **processar, analisar e consultar contratos jurídicos** de forma inteligente.

## 🔍 Funcionalidades principais

- Ingestão automatizada de contratos (PDF, DOCX)
- Vetorização com embeddings (OpenAI + LangChain)
- Armazenamento em vector store (ChromaDB)
- Extração de metadados via LLM
- Interface em Streamlit com chat sobre os contratos (RAG)
- Execução exaustiva de prompts em batch ou ad-hoc
- Armazenamento estruturado de execuções e respostas (SQLite)

## 📦 Stack utilizada

- **Python 3.11+**
- **Poetry** (gerenciador de pacotes)
- **LangChain** (orquestração LLM)
- **OpenAI GPT-4**
- **ChromaDB** (vetores)
- **SQLite / SQLAlchemy** (dados relacionais)
- **Streamlit** (frontend)
- **dotenv**, **pytest**, **loguru**

## 🧱 Estrutura de diretórios
app/
├── ingestion/ # Extração e leitura de contratos

├── processing/ # Execução de prompts e análises

├── chat/ # Módulo RAG para conversa

├── ui/ # Interface Streamlit

├── storage/ # Acesso a dados (vector + relacional)

├── config/ # Arquivos de configuração

tests/ # Testes unitários

data/ # Diretório local de contratos

## ⚙️ Como executar

# Clonar o repositório
git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
cd SEU_REPOSITORIO

# Instalar o Poetry
pip install poetry

# Instalar dependências
poetry install

# Criar .env com chave da OpenAI (exemplo no .env.example)

# Executar a API FastAPI
poetry run python api_main.py

# Rodar a interface Streamlit (a API deve estar rodando separadamente)
# Caso a API esteja em outro host/porta, defina a variável de ambiente
# `API_BASE_URL` apontando para o novo endereço.
poetry run python main.py

### Integração com VPN (opcional)

Se desejar utilizar os serviços internos de IA da Petrobras, coloque os arquivos
`petrobras-ca-root.pem` e `config-v1.x.ini` no diretório `app/config`. Caso
precise apontar para outro local, defina as variáveis `VPN_CERT_PATH` e
`VPN_CONFIG_FILE` com os caminhos completos de cada arquivo.

## 📑 Rotas da API

| Rota | Método | Descrição | Parâmetros | Retorno |
|------|--------|-----------|------------|---------|
| `/ingest` | POST | Inicia a ingestão de arquivos no diretório `data` | nenhum | `{"status": "ok"}` |
| `/ingest-structured` | POST | Carrega o CSV de contratos estruturados | nenhum | `{"status": "ok", "progress": n}` |
| `/chat` | POST | Consulta o chatbot sobre os contratos | `question` no corpo | `{"answer": str, "sources": []}` |
| `/contracts` | GET | Lista todos os contratos armazenados | nenhum | `{"contracts": [...]}` |
| `/contract/{id}` | GET | Recupera um contrato pelo código | nenhum | `{...}` |
| `/executions` | GET | Lista execuções de tarefas | `status`, `start`, `end` | `{"executions": [...]}` |
| `/executions/{id}` | GET | Detalha uma execução específica | nenhum | `{...}` |
| `/prompts` | POST | Cadastra novo prompt | `nome`, `texto`, `periodicidade` | `{"id": n}` |
| `/prompts` | GET | Lista todos os prompts | nenhum | `{"prompts": [...]}` |
| `/prompts/{id}` | GET | Consulta um prompt | nenhum | `{...}` |
| `/prompts/{id}` | PUT | Atualiza um prompt | campos do prompt | `{"status": "ok"}` |
| `/prompts/{id}` | DELETE | Remove um prompt | nenhum | `{"status": "ok"}` |

Este projeto está em desenvolvimento contínuo. As tecnologias utilizadas estão organizadas de forma modular para permitir futura substituição de bancos e serviços (ex: ChromaDB por OpenSearch, SQLite por Cloud SQL, etc).
