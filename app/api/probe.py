from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.jobs.probe_master import probe_master
from app.utils.log import app_logger
from app.schemas.probe import ProbeResponse

router = APIRouter(tags=["Probing"])


@router.post(
    "/probe",
    response_model=ProbeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger manual probe job",
    description="Schedules a background job to probe all subdomains in the master table. "
                "The job runs asynchronously and probes subdomains concurrently.",
    responses={
        202: {
            "description": "Probe job successfully scheduled",
            "model": ProbeResponse,
        },
        500: {
            "description": "Internal server error while scheduling probe job",
        },
    },
)
async def probe_now(
    background_tasks: BackgroundTasks,
) -> ProbeResponse:
    """Trigger the probe job manually (runs in background).
    
    This endpoint schedules a background task that will:
    - Fetch all subdomains from the master table
    - Probe each subdomain for liveness (HTTP/HTTPS)
    - Update the database with probe results
    - Send notifications for newly discovered alive subdomains
    
    Returns:
        ProbeResponse with status and message
    
    Raises:
        HTTPException: If there's an error scheduling the probe job
    """
    try:
        # Schedule the background task to probe all subdomains
        background_tasks.add_task(probe_master)
        
        app_logger.info("api.probe.scheduled")
        
        return ProbeResponse(
            status="scheduled",
            message="Probe job scheduled for all subdomains",
        )
    except Exception as e:
        # Log the full exception for debugging
        app_logger.error("api.probe.error", error=str(e), exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule probe job. Please try again later.",
        )
