from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.subdomain_search import router as subdomain_search
from app.init_db import init_db # opcional
from app.jobs.scheduler import start_scheduler, shutdown_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    init_db()
    start_scheduler()
    yield
    # Shutdown logic (opcional)
    shutdown_scheduler()

app = FastAPI(lifespan=lifespan)

# Incluir rutas
app.include_router(subdomain_search)

    