from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse, RedirectResponse
from starlette import status
from models import Base
from database import engine
from routers.auth import router as auth_router
from routers.todo import router as todo_router

app = FastAPI()
#frontend için
app.mount("/static", StaticFiles(directory="static"), name="static")
#tarayıcı istekleri için kullandık
@app.get("/")
def read_root(request: Request):
    return RedirectResponse(url="/todo/todo-page", status_code=status.HTTP_302_FOUND)


app.include_router(auth_router)
app.include_router(todo_router)


Base.metadata.create_all(bind=engine) #veritabanı olustur dedik

