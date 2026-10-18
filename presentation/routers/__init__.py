from fastapi import APIRouter
from presentation.routers.usuario_router import router as usuario_router
from presentation.routers.gremio_router import router as gremio_router
from presentation.routers.auth_router import router as auth_router
from presentation.routers.membro_router import router as membro_router
from presentation.routers.cargo_router import router as cargo_router
from presentation.routers.canal_router import (
    router as canal_router,
    gremio_canais_router,
)
from presentation.routers.mensagem_router import router as mensagem_router

api_router = APIRouter()

api_router.include_router(usuario_router)
api_router.include_router(gremio_router)
api_router.include_router(auth_router)
api_router.include_router(membro_router)
api_router.include_router(cargo_router)
api_router.include_router(gremio_canais_router)
api_router.include_router(canal_router)
api_router.include_router(mensagem_router)
