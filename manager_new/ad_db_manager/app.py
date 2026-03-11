from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import ad_db_manager.storage as storage
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@app.get("/",response_class=HTMLResponse)
def index(request:Request):
    return templates.TemplateResponse("index.html",{"request":request})

@app.get("/api/dtc")
def list_dtc(q:str=""):
    items=storage.load_all()
    if q:
        items=[i for i in items if q.lower() in i["code"].lower() or q.lower() in i.get("definition","").lower()]
    return items

@app.get("/api/dtc/{code}")
def get_dtc(code:str):
    f=storage.find(code)
    if not f:
        raise HTTPException(404)
    return storage.load_yaml(f)

@app.post("/api/dtc")
def create_dtc(data:dict):
    code=data["code"]
    manufacturer=data["scope"]["manufacturer"]
    if isinstance(manufacturer,list):
        manufacturer=manufacturer[0]
    p=storage.create(code,manufacturer,data)
    return {"created":str(p)}

@app.put("/api/dtc/{code}")
def update_dtc(code:str,data:dict):
    f=storage.find(code)
    if not f:
        raise HTTPException(404)
    storage.update(f,data)
    return {"updated":code}

@app.delete("/api/dtc/{code}")
def delete_dtc(code:str):
    storage.delete(code)
    return {"deleted":code}