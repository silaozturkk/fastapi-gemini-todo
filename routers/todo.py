from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Path, HTTPException, Request
from starlette import status
from starlette.responses import RedirectResponse
from models import Todo
from database import SessionLocal # SessionLocal ile veritabanına bağlantı sağlarız.
from typing import Annotated #depend için
from routers.auth import get_current_user
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/todo", #basına "todo/" koyar
    tags=["Todo"] #auth ile ayırmak için baslık
)

#frontend için
templates = Jinja2Templates(directory="templates")

#post islemi için kendi modelimizi olusturduk.
class TodoRequestModel(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool



#hazır fonk.
# bu fonksiyon her api isteği için veritabanu bağlantısını açar ve işi bitince kapatır.
# tekrar tekrar yazmamak için tek fonk. yazdık.
def get_db():
    db = SessionLocal() #veritabanıyla konusacağımız oturumu oluşturur.
    try:
        yield db #return gibi db yi döndürür returndan daha kapsamlı.
    finally:
        db.close() # işimiz bitince kapatmak için veritabanı patlamasın diye

# yine tekrar tekrar yazmamak için
# yani bu demek oluyor ki: bir endpoint içinde db_dependency kullanırsam, get_db fonksiyonunu çalıştır.
# bana bir SessionLocal veritabanı oturumu ver. Tipi SessionLocal olacak ve bu get_db ye bağlı olacak.
db_dependency = Annotated[SessionLocal, Depends(get_db)]

user_dependency = Annotated[dict, Depends(get_current_user)] #dogrulama için fonksiyonuy getiriyoruz.

#kullanıcı bulunamazsa çalıstıracağımız fonksiyon
def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page",status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie("access_token")
    return redirect_response


#frontend için
@router.get("/todo-page")
async def render_todo_page(request: Request, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        todos = db.query(Todo).filter(Todo.owner_id == user.get('id')).all()
        return templates.TemplateResponse("todo.html",{"request": request, "todos":todos, "user":user})
    except:
        return redirect_to_login()

@router.get("/add-todo-page")
async def render_add_todo_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        return templates.TemplateResponse("add-todo.html",{"request": request, "user":user})
    except:
        return redirect_to_login()

@router.get("/edit-todo-page/{todo_id}")
async def render_todo_page(request: Request, todo_id: int, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()

        todo = db.query(Todo)\
            .filter(Todo.id == todo_id)\
            .filter(Todo.owner_id == user.get("id"))\
            .first()

        if todo is None:
            return redirect_to_login()

        return templates.TemplateResponse(
            "edit-todo.html",
            {"request": request, "todo": todo, "user": user}
        )

    except:
        return redirect_to_login()

# bu fonksiyonun çalışması için bir user a ihtiyac var ve bunu da user_dependency i çalıştırarak bul deriz.
@router.get("/")
async def read_all(user: user_dependency, db: db_dependency ): # bu fonksiyon su db yi kullanacak diyoruz.
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.query(Todo).filter(Todo.owner_id == user.get('id')).all()# o kullanıcının butun Todolarını getir.


# id ye göre filtreleme
@router.get("/todo/{todo_id}",status_code=status.HTTP_200_OK)
async def read_by_id(user: user_dependency, db: db_dependency , todo_id: int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    #todo id eslesmesi ve kullanıcı eslesmesi yaptık sızıntılara karşı çift aşamalı kontrol
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first()

    if todo is not None:
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

#ekleme
@router.post("/todo", status_code=201)
async def create_todo(request: Request, db: db_dependency, todo_request: TodoRequestModel):

    token = request.cookies.get("access_token")
    user = await get_current_user(token)

    todo = Todo(**todo_request.dict(), owner_id=user.get("id"))

    db.add(todo)
    db.commit()

@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency,db: db_dependency,
                      todo_request: TodoRequestModel,
                      todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    todo.title = todo_request.title
    todo.description = todo_request.description
    todo.priority = todo_request.priority
    todo.complete = todo_request.complete

    db.add(todo)
    db.commit()


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    #db.query(Todo).filter(Todo.id == todo_id).delete()
    db.delete(todo)
    db.commit()