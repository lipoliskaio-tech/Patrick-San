"""
Ponto de entrada da aplicação FastAPI.

Para rodar em desenvolvimento:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Para rodar em produção (Render/Railway/VPS):
    uvicorn main:app --host 0.0.0.0 --port $PORT
"""
import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError

from database.database import Base, engine
import models  # noqa: F401 - garante que todos os modelos sejam registrados
from routers import auth, admin, client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("license_system")

# Cria as tabelas automaticamente caso ainda não existam.
# Em produção recomenda-se usar Alembic (veja backend/alembic) para migrações controladas.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Licenciamento",
    description="API completa para gerenciamento de licenças de software.",
    version="1.0.0",
)

# --- Rate limiting global ---------------------------------------------------
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS --------------------------------------------------------------------
# Ajuste allow_origins para o domínio real do seu painel em produção.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Tratamento de erros -----------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Erro de validação em {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "detail": "Dados inválidos.", "errors": exc.errors()},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Erro de banco de dados em {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "detail": "Erro interno no banco de dados."},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erro não tratado em {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "detail": "Erro interno do servidor."},
    )


# --- Middleware de log de requisições ----------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path} - IP: {request.client.host if request.client else 'desconhecido'}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code}")
    return response


# --- Rotas --------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(client.router)


@app.get("/", tags=["Status"])
def root():
    return {"status": "online", "service": "Sistema de Licenciamento"}


@app.get("/health", tags=["Status"])
def health_check():
    return {"status": "healthy"}
