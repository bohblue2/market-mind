from fastapi import APIRouter

from .v1 import chat, root, securities 

router = APIRouter(
    prefix="/api",
)

router.include_router(chat.router)
router.include_router(root.router)
router.include_router(securities.router)