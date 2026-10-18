from fastapi import APIRouter
from presentation.routers.usuario_router import router as usuario_router
from presentation.routers.gremio_router import router as gremio_router
from presentation.routers.auth_router import router as auth_router

api_router = APIRouter()

api_router.include_router(usuario_router)
api_router.include_router(gremio_router)
api_router.include_router(auth_router)