import uuid

from fastapi import APIRouter, BackgroundTasks, Request

from ..models.sandbox_model import GitUrl, submission
from ..sandbox import judge as judge_sandbox

router = APIRouter()


@router.get('/sandbox/heartbeat')
async def heartbeat(request: Request):
    return {'status': 'ok', 'available_sandboxes': len(request.app.state.available_box)}


@router.post('/judge')
async def judgeRepo(repo_url: GitUrl, background_tasks: BackgroundTasks, request: Request):
    task = submission(url=repo_url.url, uuid=uuid.uuid4())
    if len(request.app.state.available_box) == 0:
        request.app.state.waiting.put_nowait(task)
        return {
            'status': 'waiting',
            'position': request.app.state.waiting.qsize(),
            'uuid': task.uuid,
        }
    else:
        sandbox_number = request.app.state.available_box.pop()

        background_tasks.add_task(judge_sandbox.judge, request.app.state, sandbox_number, task)
        return {'status': 'judging', 'uuid': task.uuid}
