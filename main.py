from pydantic import BaseModel, Field
from fastapi import FastAPI, Depends, Path, HTTPException
from starlette import status

from models import Base, Todo
from sqlalchemy.orm import Session
from database import engine, SessionLocal # SessionLocal ile veritabanına bağlantı sağlarız.
from typing import Annotated #depend için


app = FastAPI()

Base.metadata.create_all(bind=engine) #veritabanı olustur dedik

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

@app.get("/read_all")
async def read_all(db: db_dependency ): # bu fonksiyon su db yi kullanacak diyoruz.
    return db.query(Todo).all() # Todo tablosundaki tüm veriyi getir.


# id ye göre filtreleme
@app.get("/get_by_id/{todo_id}",status_code=status.HTTP_200_OK)
async def get_read_by_id(db: db_dependency , todo_id: int=Path(gt=0)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first() # buldugun ilk eslesmeyi getir dedik
    if todo is not None:
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

#ekleme
@app.post("/create_todo",status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, todo_request: TodoRequestModel):
    todo = Todo(**todo_request.dict())
    db.add(todo)
    db.commit()

@app.put("/update_todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
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

@app.delete("/delete_todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    db.query(Todo).filter(Todo.id == todo_id).delete()
    db.commit()