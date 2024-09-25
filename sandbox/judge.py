import shutil

import git
from dotenv import dotenv_values

from ..models.sandbox_model import submission
from ..utils.isolate import sandbox, sandbox_result


def check_available(state):
    if len(state.available_box) == 0 or state.waiting.empty():
        return
    next_task = state.waiting.get_nowait()
    judge(state, state.available_box.pop(), next_task.url, next_task.uuid)


def judge(state, sandbox_number: int, task: submission):
    def end_judging(repo_folder):
        shutil.rmtree(repo_folder, ignore_errors=True)
        state.judging[sandbox_number] = None
        state.available_box.add(sandbox_number)
        check_available(state)

    print(f'Judging {task.url} in sandbox {sandbox_number}')
    state.judging[sandbox_number] = task.url

    repo_name = task.uuid
    repo_folder = f'/tmp/sandbox-api/{repo_name}'
    try:
        git.Repo.clone_from(task.url, repo_folder)
    except git.exc.GitCommandError as e:
        end_judging(repo_folder)
        print({'status': 'error', 'message': str(e.stderr).split('\n')[2]})
    # do some judging
    box = sandbox(sandbox_number, dotenv_values('.env')['ENABLE_CGROUP'])
    result: sandbox_result = box.run(['/usr/bin/echo', 'Hello, World!'], 1)
    print(result)
    end_judging(repo_folder)
    return {'status': 'judged'}
