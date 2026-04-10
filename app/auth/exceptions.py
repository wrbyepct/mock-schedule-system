from fastapi import Request, status
from fastapi.responses import JSONResponse


class UserExistsError(Exception):
    """Error when there is already user existing in db."""

    @staticmethod
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        detail = {"detail": "The same email has been registered."}
        return JSONResponse(content=detail, status_code=status.HTTP_409_CONFLICT)
