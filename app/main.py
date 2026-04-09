from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.shared.database import engine, init_db

from .routers import add_all_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await engine.dispose()


version = "v1"

app = FastAPI(
    title="Medical Scheduler",
    description="Medical Scheduler",
    version=version,
    lifespan=lifespan,
)

add_all_routers(app)


@app.get("/health", tags=["health"])
def health():
    return {"status": "Healthy"}
