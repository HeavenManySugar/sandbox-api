import uuid

from fastapi import APIRouter, BackgroundTasks, Request

from ..models.sandbox_model import GitUrl, submission

router = APIRouter()


@router.get('/sandbox/heartbeat')
async def heartbeat(request: Request):
    return {
        'status': 'ok',
        'available_sandboxes': len(request.app.state.available_box),
        'waiting_tasks': request.app.state.judge_system.get_waiting_length(),
        'judging_tasks': request.app.state.judge_system.get_judging_length(),
    }


@router.post('/judge')
async def judgeRepo(repo_url: GitUrl, background_tasks: BackgroundTasks, request: Request):
    task = submission(url=repo_url.url, uuid=uuid.uuid4())
    if request.app.state.judge_system.add_task(background_tasks, task):
        return {
            'status': 'waiting',
            'position': request.app.state.judge_system.get_waiting_length(),
            'uuid': task.uuid,
        }
    else:
        return {'status': 'judging', 'uuid': task.uuid}
