
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_layer import router as ai_router
from routes.accounts import router as accounts_router
from routes.conversations import router as conversations_router
from routes.tasks import router as tasks_router
from routes.portfolio_config import router as portfolio_config_router

app = FastAPI(title="Human-in-Loop Collections")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(ai_router)
app.include_router(accounts_router)
app.include_router(conversations_router)
app.include_router(tasks_router)
app.include_router(portfolio_config_router)


@app.get("/health", tags=["Health"])
async def health():
    """Simple liveness check."""
    return {"status": "ok"}