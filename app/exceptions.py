from __future__ import annotations

from typing import TYPE_CHECKING

from app.auth.exceptions import UserExistsError

if TYPE_CHECKING:
    from fastapi import FastAPI


all_exceptions = [UserExistsError]


def register_all_exceptions(app: FastAPI):

    for exc in all_exceptions:
        app.add_exception_handler(
            exc,
            handler=exc.handler,
        )
