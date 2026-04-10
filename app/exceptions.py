from fastapi import FastAPI

from app.auth.exceptions import UserExistsError

all_exceptions = [UserExistsError]


def register_all_exceptions(app: FastAPI):

    for exc in all_exceptions:
        app.add_exception_handler(
            exc,
            handler=exc.handler,
        )
