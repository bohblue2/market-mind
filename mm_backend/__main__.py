from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mm_backend.config import settings
from mm_backend.database.session import init_db
from mm_backend.routers.api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initializes the database tables when the application starts up.
    """
    init_db()
    yield

def get_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    if settings.DEBUG:
        origins = ["*"]
    else:
        origins = [
            str(origin).strip(",") for origin in settings.ORIGINS 
        ]

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router=router)
    
    return app  

app = get_app()
@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    app = get_app()
    uvicorn.run(app, host="127.0.0.1", port=8080)

    
    
