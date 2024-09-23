from fastapi import FastAPI

from .routers import sandbox

app = FastAPI()


@app.get('/')
def read_root():
    return {'Hello': 'World'}
