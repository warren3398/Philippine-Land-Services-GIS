"""Unified Philippine Land Services GIS Portal v2.0 — one ASGI server."""
import importlib.util
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.wsgi import WSGIMiddleware
from slope_api import app

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pls_harmonizer',ROOT/'modules'/'harmonizer_v2_8_1'/'app.py')
harmonizer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(harmonizer)
app.mount('/harmonizer',WSGIMiddleware(harmonizer.app))
app.mount('/eo79',StaticFiles(directory=str(ROOT/'static'/'eo79'),html=True),name='eo79')
@app.get('/',include_in_schema=False)
def homepage():
    return FileResponse(ROOT/'templates'/'index.html')
