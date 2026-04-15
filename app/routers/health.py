from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Public health check endpoint for deploy platforms and uptime probes.",
    operation_id="getHealth",
)
def get_health():
    return {"status": "ok"}