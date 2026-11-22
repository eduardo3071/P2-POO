from fastapi import FastAPI

from app.routes.chamados import router
from app.routes.erros import registrar_tratadores

app = FastAPI(title="Chamados de TI do campus", version="1.0.0")
registrar_tratadores(app)
app.include_router(router)
