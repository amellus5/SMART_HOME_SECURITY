
from fastapi import FastAPI

from backend.app.api.member_routes import router as member_router
from backend.app.api.event_routes import router as event_router
from backend.app.api.camera_routes import router as camera_router

app = FastAPI(
    title="SMART HOME SECURITY API",
    description="API he thong giam sat an ninh nha o thong minh",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "SMART HOME SECURITY API IS RUNNING!",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Smart Home Security Backend"
    }


app.include_router(member_router)
app.include_router(event_router)
app.include_router(camera_router)
