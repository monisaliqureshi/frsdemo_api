from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from routes.user import user
from config.auth import auth
from fastapi_jwt_auth.exceptions import AuthJWTException
import sys
sys.setrecursionlimit(1500)

app = FastAPI(title="Face Recognition APIs", docs_url="/documentation")


app.include_router(user)
# app.include_router(auth)

@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

