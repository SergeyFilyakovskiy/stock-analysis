from fastapi import APIRouter
from .endpoints.auth import router as auth_router
from .endpoints.oauth import router as oauth_router
from .endpoints.verify import router as verify_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(oauth_router)
v1_router.include_router(verify_router)