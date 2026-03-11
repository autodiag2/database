import yaml
from pathlib import Path
from ad_db_manager.log import logger

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data-src"

def dtc_files():
    return list(DATA_ROOT.rglob("*.yml"))

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def save_yaml(path,data):
    with open(path,"w") as f:
        yaml.safe_dump(data,f,sort_keys=False)

def load_all():
    out=[]
    for f in dtc_files():
        d=load_yaml(f)
        d["_path"]=str(f)
        out.append(d)
    return out

def find(code):
    for f in dtc_files():
        if f.stem.upper() == code.upper():
            return f
    return None

def create(code, manufacturer, data):
    p=DATA_ROOT / "vehicle" / manufacturer.lower() / "dtc"
    p.mkdir(parents=True,exist_ok=True)
    file=p / f"{code}.yml"
    save_yaml(file,data)
    return file

def update(path,data):
    save_yaml(path,data)

def delete(code):
    f=find(code)
    if f:
        f.unlink()