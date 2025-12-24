from fastapi import APIRouter, BackgroundTasks, Query, HTTPException
from typing import Optional

from app.jobs.probe_master import probe_master
from app.utils.log import app_logger

router = APIRouter(tags=["Probing"])


@router.post("/probe")
async def probe_now(background_tasks: BackgroundTasks, limit: Optional[int] = Query(None, description="Limit number of subdomains to probe")):
    """Trigger the probe job manually (runs in background).

    - `limit` optionally limits the number of subdomains probed in this run.
    """
    try:
        background_tasks.add_task(probe_master, limit=limit)
        app_logger.info("api.probe.scheduled", limit=limit)
        return {"status": "probe scheduled", "limit": limit}
    except Exception as e:
        app_logger.error("api.probe.error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
