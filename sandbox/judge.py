import shutil
import subprocess
import time

import git

from ..models.sandbox_model import submission


def check_available(state):
    if len(state.available_box) == 0 or state.waiting.empty():
        return
    next_task = state.waiting.get_nowait()
    judge(state, state.available_box.pop(), next_task.url, next_task.uuid)


def judge(state, sandbox_number: int, task: submission):
    def end_judging(repo_folder):
        shutil.rmtree(repo_folder)
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
        return {'status': 'error', 'message': str(e.stderr).split('\n')[2]}
    # do some judging
    try:
        subprocess.run(
            [
                'isolate',
                '--box-id',
                str(sandbox_number),
                '--processes',
                '--full-env',
                '--run',
                '--',
                '/usr/bin/echo',
                'Hello, World!',
            ],
            cwd=repo_folder,
            timeout=1,
        )
    except subprocess.TimeoutExpired:
        print(f'Timeout for {task.url} in sandbox {sandbox_number}')
        end_judging(repo_folder)
        return {'status': 'timeout'}
    end_judging(repo_folder)
    return {'status': 'judged'}
