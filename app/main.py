from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.shared.database import engine, init_db

from .exceptions import register_all_exceptions
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
register_all_exceptions(app)

# TODO: Registration related models: TimestampMixin, Department, User, SkillTag(System), UserSkillTag(This skill is possesed by what users)
# TODO: Register logic


@app.get("/health/", tags=["health"])
def health():
    return {"status": "Healthy!"}
