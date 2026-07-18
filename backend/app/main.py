from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.catalog.router import router as catalog_router
from app.config import settings
from app.orders.router import router as orders_router
from app.users.router import auth_router, users_router

# Importar todos os models para registrar no SQLAlchemy
import app.users.models  # noqa: F401
import app.catalog.models  # noqa: F401
import app.orders.models  # noqa: F401

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded



app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# "Liga" o limitador na aplicação
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app = FastAPI(title="Caixa Mágica API", version="0.1.0")

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


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "Caixa Mágica API"}
