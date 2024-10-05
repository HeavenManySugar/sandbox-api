import shutil
from contextlib import asynccontextmanager

from dotenv import dotenv_values
from fastapi import FastAPI

from .routers import sandbox
from .sandbox.judge import JudgeSystem
from .utils.isolate import cleanup_sandbox, init_sandbox


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Do something at the start of the lifespan
    app.state.available_box = set()

    SANDBOX_NUMBER = dotenv_values('.env')['SANDBOX_NUMBER']
    ENABLE_CGROUP = dotenv_values('.env')['ENABLE_CGROUP']
    for i in range(int(SANDBOX_NUMBER)):
        print(f'Initializing sandbox {i}')
        r = init_sandbox(box_id=i, cg=(ENABLE_CGROUP == 'True'))
        if r.returncode != 0:
            print(f'Error initializing sandbox {i}')
            print(r.stderr)
        else:
            app.state.available_box.add(i)
    app.state.judge_system = JudgeSystem(app.state)
    yield
    # Do something at the end of the lifespan
    for i in range(int(SANDBOX_NUMBER)):
        print(f'Cleaning up sandbox {i}')
        cleanup_sandbox(box_id=i, cg=(ENABLE_CGROUP == 'True'))
    # shutil.rmtree('/tmp/sandbox-api', ignore_errors=True)


app = FastAPI(lifespan=lifespan)


@app.get('/')
def read_root():
    return {'Hello': 'World'}


app.include_router(sandbox.router)
