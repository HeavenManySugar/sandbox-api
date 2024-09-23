import shutil
import time
import uuid

import git


def check_available(state):
    if len(state.available_box) == 0 or state.waiting.empty():
        return
    judge(state, state.available_box.pop(), state.waiting.get_nowait().url)


def judge(state, sandbox_number: int, repo_url: str):
    print(f'Judging {repo_url} in sandbox {sandbox_number}')
    state.judging[sandbox_number] = repo_url

    # print(repo_url)
    repo_name = uuid.uuid4()
    repo_folder = f'./tmp_repo/{repo_name}'
    # print(repo_name)
    try:
        git.Repo.clone_from(repo_url, repo_folder)
    except git.exc.GitCommandError as e:
        return {'status': 'error', 'message': str(e.stderr).split('\n')[2]}
    # do some judging
    time.sleep(1)
    shutil.rmtree(repo_folder)
    state.available_box.add(sandbox_number)
    check_available(state)
    return {'status': 'judged'}
