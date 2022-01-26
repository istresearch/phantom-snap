# entrypoint.py
from fastapi import FastAPI, Body
from typing import Any, Dict, AnyStr, List, Union
import sys
from handler import PageRenderer
sys.path.insert(0, '/phantom_snap')

renderer = PageRenderer()

app = FastAPI()

@app.post("/")
async def handle(request: Dict[Any, Any]):
    return renderer.render({"body": request})

