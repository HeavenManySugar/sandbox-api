from fastapi import APIRouter, BackgroundTasks, Request

from ..models.git import GitUrl
from ..sandbox import judge as judge_sandbox

router = APIRouter()


@router.get('/sandbox/heartbeat')
async def heartbeat(request: Request):
    return {'status': 'ok', 'available_sandboxes': len(request.app.state.available_box)}


@router.post('/judge')
async def judgeRepo(repo_url: GitUrl, background_tasks: BackgroundTasks, request: Request):
    if len(request.app.state.available_box) == 0:
        request.app.state.waiting.put_nowait(repo_url)
        return {'status': 'waiting', 'position': request.app.state.waiting.qsize()}
    else:
        sandbox_number = request.app.state.available_box.pop()
        background_tasks.add_task(
            judge_sandbox.judge,
            request.app.state,
            sandbox_number,
            repo_url.url,
        )
        return {'status': 'judging'}
