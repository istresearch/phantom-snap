# main.py

from fastapi import FastAPI, Request
from typing import Any, Dict, AnyStr, List, Union
import sys
from render import PageRenderer
sys.path.insert(0, '/phantom_snap')

renderer = PageRenderer()

app = FastAPI()

@app.post("/")
async def render_page(request: Request):
    return renderer.render(await request.json())
