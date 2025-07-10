from app.api import app
import uvicorn

# Arquivo de inicialização da API FastAPI

# Executa a API em modo standalone quando chamado diretamente
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
