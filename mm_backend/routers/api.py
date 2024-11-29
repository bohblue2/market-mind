from fastapi import APIRouter

from .v1 import root, securities

router = APIRouter(
    prefix="/api",
)

router.include_router(root.router)
router.include_router(securities.router)