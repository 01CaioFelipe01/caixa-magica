from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from app.core.responses import error_response

class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Recurso não encontrado"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Não autorizado"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class BadRequestException(HTTPException):
    def __init__(self, detail: str = "Requisição inválida"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ConflictException(HTTPException):
    def __init__(self, detail: str = "Conflito"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

async def global_exception_handler(request: Request, exc: Exception):
    
    corpo = error_response(
        code="INTERNAL_SERVER_ERROR", 
        message="Ocorreu um erro interno no servidor. Tente novamente mais tarde."
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=corpo
    )