from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from model.index import account_user
from config.db import conn
from schemas.users import AccountUser
import datetime

auth = APIRouter()

class User(BaseModel):
    username: str
    password: str

class Settings(BaseModel):
    authjwt_secret_key: str = "secret"
    # Configure algorithms which is permit
    authjwt_decode_algorithms: set = {"HS384","HS512"}

@AuthJWT.load_config
def get_config():
    return Settings()

@auth.post('/login')
async def login(user: User):
    """

    access_token --> For accessing secure endpoints
    refresh token --> For accessing the refresh endpoint to refresh access token
    """
    try:
        data = conn.execute(account_user.select().where(account_user.c.name == user.username and account_user.c.password == user.password)).fetchone()
        return {"access_token": data[-2], "refresh_token": data[-1]}
    except:
        return {"res": False, "msg":"username of password is incorrect."}
# In protected route, automatically check incoming JWT
# have algorithm in your `authjwt_decode_algorithms` or not
@auth.post('/refresh_token')
async def refresh(Authorize: AuthJWT = Depends()):
    Authorize.jwt_refresh_token_required()

    current_user = Authorize.get_jwt_subject()
    new_access_token = Authorize.create_access_token(subject=current_user)
    return {"access_token": new_access_token}

@auth.get('/user')
async def user(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()

    current_user = Authorize.get_jwt_subject()
    return {"user": current_user}

@auth.post("/signup")
async def signup(new_user: AccountUser, Authorize: AuthJWT = Depends()):
    exist_usersname = conn.execute(account_user.select().where(account_user.c.name == new_user.username)).fetchall()
    exist_email = conn.execute(account_user.select().where(account_user.c.email == new_user.email)).fetchall()
    if len(exist_usersname) == 0 and len(exist_email) == 0:
        access_token = Authorize.create_access_token(subject=new_user.username,algorithm="HS384", expires_time = datetime.timedelta(days = 30))
        refresh_token = Authorize.create_refresh_token(subject=new_user.username,algorithm="HS512")
        conn.execute(account_user.insert().values(
            name=new_user.username,
            email=new_user.email,
            password=new_user.password,
            access_token=access_token,
            refresh_token=refresh_token
        ))
        return {"res": True, "msg": "Registration completed", "access_token": access_token, "refresh_token": refresh_token}
    elif len(exist_email)!=0:
        return {"res": False, "msg": "Email already exist", "access_token": "", "refresh_token": ""}
    elif len(exist_usersname)!=0:
        return {"res": False, "msg": "Username already exist", "access_token": "", "refresh_token": ""}
    else:
        return {"res": False, "msg": "Email or Username already exist", "access_token": "", "refresh_token": ""}

@auth.get("/login_users_list")
async def login_users_list(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()

    return conn.execute(account_user.select()).fetchall()