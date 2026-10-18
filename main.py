from infra.database import engine, Base, SessionLocal

from application.usuario_service import UsuarioService
from infra.core.repositories import UsuarioRepository
from domain.core import Usuario

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from presentation.routers import api_router

def init_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

init_db()

app = FastAPI(
    title="ELO API",
    description="Backend do sistema ELO integrado com React",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/", tags=["Health Check"])
def health_check():
    return {"status": "ok", "mensagem": "API ELO rodando com sucesso!"}