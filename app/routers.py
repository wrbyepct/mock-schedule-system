from __future__ import annotations

from typing import TYPE_CHECKING

from app.auth.router import auth_router

if TYPE_CHECKING:
    from fastapi import FastAPI

all_routers = [auth_router]


def add_all_routers(app: FastAPI):
    for router in all_routers:
        app.include_router(router, prefix="/api")
