from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.controllers.recursive_search_controller import router as recursive_search_router
from app.init_db import init_db # opcional

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    init_db()
    yield
    # Shutdown logic (opcional)

app = FastAPI(lifespan=lifespan)

# Incluir rutas
app.include_router(recursive_search_router)


    