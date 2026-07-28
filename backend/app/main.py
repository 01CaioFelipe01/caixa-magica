from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.catalog.router import router as catalog_router
from app.config import settings
from app.orders.router import router as orders_router
from app.users.router import auth_router, users_router

# Importar todos os models para registrar no SQLAlchemy
import app.users.models  # noqa: F401
import app.catalog.models  # noqa: F401
import app.orders.models  # noqa: F401


app = FastAPI(title="Caixa Mágica API", version="0.1.0")

uploads_dir = Path(settings.UPLOADS_DIR)
try:
    uploads_dir.mkdir(parents=True, exist_ok=True)
except OSError:
    # Filesystem somente leitura (ambiente serverless): segue sem mount.
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
if uploads_dir.is_dir():
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "Caixa Mágica API"}
