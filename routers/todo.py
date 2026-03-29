from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Path, HTTPException
from starlette import status

from models import Todo
from database import SessionLocal # SessionLocal ile veritabanına bağlantı sağlarız.
from typing import Annotated #depend için
from routers.auth import get_current_user

router = APIRouter(
    prefix="/todo", #basına "todo/" koyar
    tags=["Todo"] #auth ile ayırmak için baslık
)

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

# bu fonksiyonun çalışması için bir user a ihtiyac var ve bunu da user_dependency i çalıştırarak bul deriz.
@router.get("/")
async def read_all(user: user_dependency, db: db_dependency ): # bu fonksiyon su db yi kullanacak diyoruz.
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.query(Todo).filter(Todo.owner_id == user.get('id')).all()# o kullanıcının butun Todolarını getir.


# id ye göre filtreleme
@router.get("/get_by_id/{todo_id}",status_code=status.HTTP_200_OK)
async def get_read_by_id(db: db_dependency , todo_id: int=Path(gt=0)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first() # buldugun ilk eslesmeyi getir dedik
    if todo is not None:
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

#ekleme
@router.post("/create_todo",status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequestModel):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    # todoyu kaydederken kullanıcı id sini de alıyorum. bunu da json web tokendan almıstım
    todo = Todo(**todo_request.dict(), owner_id = user.get('id'))
    db.add(todo)
    db.commit()

@router.put("/update_todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db: db_dependency, todo_request: TodoRequestModel, todo_id: int=Path(gt=0)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    todo.title = todo_request.title
    todo.description = todo_request.description
    todo.priority = todo_request.priority
    todo.complete = todo_request.complete

    db.add(todo)
    db.commit()

@router.delete("/delete_todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    db.query(Todo).filter(Todo.id == todo_id).delete()
    db.commit()