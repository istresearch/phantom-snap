# main.py

from fastapi import FastAPI, Body
from typing import Any, Dict, AnyStr, List, Union
import sys
from pydantic import BaseModel
from render import PageRenderer
sys.path.insert(0, '/phantom_snap')

renderer = PageRenderer()

app = FastAPI()

# class Data(BaseModel):
#     url: str

@app.post("/")
async def handle(request: Dict[Any, Any]):
    #return (request)
    return renderer.render({"body": request})

# renderer = PageRenderer()
#
# app = FastAPI()
#
# @app.post("/")
# async def render_page(request: Request):
#     return renderer.render(await request.body())
