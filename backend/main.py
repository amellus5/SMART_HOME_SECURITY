
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.member_routes import router as member_router
from backend.app.api.event_routes import router as event_router
from backend.app.api.camera_routes import router as camera_router


# ========================================
# DUONG DAN CAC THU MUC
# ========================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
STORAGE_DIR = PROJECT_ROOT / "storage"


# ========================================
# KHOI TAO FASTAPI
# ========================================

app = FastAPI(
    title="SMART HOME SECURITY API",
    description="API he thong giam sat an ninh nha o thong minh",
    version="1.0.0"
)


# ========================================
# PHUC VU GIAO DIEN WEBSITE
# ========================================

app.mount(
    "/css",
    StaticFiles(directory=FRONTEND_DIR / "css"),
    name="css"
)

app.mount(
    "/js",
    StaticFiles(directory=FRONTEND_DIR / "js"),
    name="js"
)


# ========================================
# PHUC VU ANH VA DU LIEU STORAGE
# ========================================

app.mount(
    "/storage",
    StaticFiles(directory=STORAGE_DIR),
    name="storage"
)


# ========================================
# TRANG CHU
# ========================================

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


# ========================================
# KIEM TRA TRANG THAI BACKEND
# ========================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Smart Home Security Backend"
    }


# ========================================
# DANG KY CAC API ROUTERS
# ========================================

app.include_router(member_router)
app.include_router(event_router)
app.include_router(camera_router)