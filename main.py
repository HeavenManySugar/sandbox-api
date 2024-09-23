import asyncio
import queue
import shutil
import subprocess
from contextlib import asynccontextmanager
import os

from dotenv import dotenv_values
from fastapi import FastAPI

from .routers import sandbox
from .sandbox import judge


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Do something at the start of the lifespan
    app.state.available_box = set()
    app.state.judging = {}
    app.state.waiting = queue.Queue()
    asyncio.create_task(judge.sandbox_queue(app.state))

    SANDBOX_NUMBER = dotenv_values('.env')['SANDBOX_NUMBER']
    for i in range(int(SANDBOX_NUMBER)):
        print(f'Initializing sandbox {i}')
        r = subprocess.run(['isolate', '--init', '-b', str(i)], capture_output=True)
        if r.returncode != 0:
            print(f'Error initializing sandbox {i}')
            print(r.stderr)
        else:
            app.state.available_box.add(i)
    yield
    # Do something at the end of the lifespan
    for i in range(int(SANDBOX_NUMBER)):
        print(f'Cleaning up sandbox {i}')
        subprocess.run(['isolate', '--cleanup', '-b', str(i)])
    shutil.rmtree('./tmp_repo', ignore_errors=True)


app = FastAPI(lifespan=lifespan)


@app.get('/')
def read_root():
    return {'Hello': 'World'}


app.include_router(sandbox.router)
