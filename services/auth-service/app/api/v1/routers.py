from fastapi import APIRouter

from app.api.v1.endpoints.auth   import router as auth_router
from app.api.v1.endpoints.oauth  import router as oauth_router
from app.api.v1.endpoints.verify import router as verify_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(oauth_router)
v1_router.include_router(verify_router)