from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.subdomain_search import router as subdomain_search
from app.init_db import init_db # opcional

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    init_db()
    yield
    # Shutdown logic (opcional)

app = FastAPI(lifespan=lifespan)

# Incluir rutas
app.include_router(subdomain_search)

    