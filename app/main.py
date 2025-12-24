from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.subdomain_search import router as subdomain_search
from app.api.probe import router as probe_router
from app.jobs.scheduler import start_scheduler, shutdown_scheduler, add_daily_probe_job

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    start_scheduler()
    # register daily probe job (idempotent if already present)
    add_daily_probe_job()
    yield
    # Shutdown logic (opcional)
    shutdown_scheduler()

app = FastAPI(lifespan=lifespan)

# include routes
app.include_router(subdomain_search)
app.include_router(probe_router)

    