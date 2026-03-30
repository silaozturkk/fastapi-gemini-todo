from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from database import SessionLocal
from models import User
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/auth", #authla ilgili olan herseyin basına auth koyar
    tags=["Authentication"] #docsda ayırmak için
)

templates = Jinja2Templates(directory="templates/")

#jwt için
SECRET_KEY = "kjebksbjkbegjb94u8y748wheg8ghf3n"
ALGORITHM = "HS256"

#sifreleme algoritması
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")


#veritabanına bağlanma isteği
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

class CreateUserRequestModel(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(username:str, user_id:int, role: str, expires_delta: timedelta):
    payload= {'sub': username, 'id': user_id, 'role': role}

    # bu token ne zaman gecerliliğini kaybedecek onu yazıyoruz.
    expires = datetime.now(timezone.utc) + expires_delta
    payload.update({'exp': expires})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


#kullanıcı doğrulama
def authenticate_user(username: str, password: str, db):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False #kullanıcı yoksa gec
    if not bcrypt_context.verify(password, user.hashed_password): #kullanıcının hashlanmıs sifresini kontrol ediyorus
        return False # esit değilse yanlıs döndür
    return user

# bunu kullanarak her kullanıcı eslesmesini yapabilirim
#token da gönderdiğimizi kontrol edecepiz bu fonksiyonlar
#bu fonksiyonun yazılma sebebi biri todolara erişirken o kisi mi değil mi diye kontrol yaparızç
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        user_id = payload.get('id')
        user_role = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Username or ID is invalid")
        return {'username': username, 'id': user_id, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Token is Invalid")



#frontend bağlama yani tarayıcı istek attığında istenen sayfaya yollama
@router.get("/login-page")
def render_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
#kayıt isteği
@router.get("/register-page")
def render_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/",status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency,create_user_request: CreateUserRequestModel):
    user = User(
        username=create_user_request.username,
        email=create_user_request.email,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        is_active=True,
        hashed_password=bcrypt_context.hash(create_user_request.password),
    )
    db.add(user)
    db.commit()


# fast api kullanıcı adı ve sifresini isteyen bir form olusturmus bunu import ettik. burda kullanırız.
@router.post("/token", response_model = Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm,Depends()],
                                 db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=60))
    response = RedirectResponse(url="/todo/todo-page", status_code=302)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True
    )

    return response