from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel

from typing import Annotated, Generator, Literal

from config import JWT_KEY
from printer import PrinterSession, GoDexPrinter

SECURITY = HTTPBearer(
    scheme_name="JWT",
    description="JWT which get from posting discord oauth code to /auth/login.",
    auto_error=False,
)


class JwtPayload(BaseModel):
    sub: str
    iat: int
    exp: int
    roles: list[Literal["ADMIN", "OPERATORS_READ", "OPERATORS_WRITE",
                        "OPERATION_RECORD_READ", "OPERATION_RECORD_WRITE", "PRINT_LABEL"]]


def authorization(token: HTTPAuthorizationCredentials = Depends(SECURITY)):
    try:
        jwt = token.credentials
        decode_data = JwtPayload(**decode(
            jwt=jwt,
            key=JWT_KEY,
            algorithms=["HS256"],
            options={
                "require": ["exp", "iat", "sub", "roles"]
            }
        ))

        if "PRINT_LABEL" not in decode_data.roles:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Insufficient permissions to print labels."
            )
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token."
        )


def get_printer_session() -> Generator[PrinterSession, None, None]:
    with GoDexPrinter.open() as session:
        yield session


auth_depends = Depends(authorization)

printer_depends = Depends(get_printer_session)
PrinterDepends = Annotated[PrinterSession, printer_depends]
