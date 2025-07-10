from fastapi import FastAPI

from .routes import router

# Instância principal da aplicação FastAPI

app = FastAPI()
# Registra todas as rotas da aplicação
app.include_router(router)

__all__ = ["app"]
