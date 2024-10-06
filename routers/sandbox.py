import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from ..models.sandbox_model import GitUrl, submission

router = APIRouter()


@router.get('/sandbox/heartbeat')
async def heartbeat(request: Request):
    return {
        'status': 'ok',
        'available_sandboxes': len(request.app.state.available_box),
        'waiting_tasks': await request.app.state.judge_system.get_waiting_length(),
        'judging_tasks': await request.app.state.judge_system.get_judging_length(),
    }


@router.post('/judge')
def judgeRepo(repo_url: GitUrl, background_tasks: BackgroundTasks, request: Request):
    task = submission(url=repo_url.url, uuid=uuid.uuid4())
    result = request.app.state.judge_system.add_task(background_tasks, task)
    match result:
        case 0:
            return {'status': 'judging', 'uuid': task.uuid}
        case 1:
            return {
                'status': 'waiting',
                'position': request.app.state.judge_system.get_waiting_length(),
                'uuid': task.uuid,
            }
        case 2:
            raise HTTPException(status_code=400, detail='Invalid repository URL')


@router.get('/result/{uuid}')
def get_result(uuid: uuid.UUID, request: Request):
    try:
        return request.app.state.judge_system.get_result(uuid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Result not found')


@router.get('/result/{uuid}/valgrind')
def get_valgrind(uuid: uuid.UUID, request: Request):
    try:
        return request.app.state.judge_system.get_valgrind(uuid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Result not found')


@router.get('/result/{uuid}/sandbox/grp/json')
def get_grp_json(uuid: uuid.UUID, request: Request):
    try:
        return request.app.state.judge_system.get_grp_json(uuid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Result not found')


@router.get('/result/{uuid}/sandbox/grp/text')
def get_grp_text(uuid: uuid.UUID, request: Request):
    try:
        return request.app.state.judge_system.get_grp_text(uuid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Result not found')


@router.get('/result/{uuid}/sandbox/meta')
def get_meta(uuid: uuid.UUID, request: Request):
    try:
        return request.app.state.judge_system.get_meta(uuid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Result not found')
