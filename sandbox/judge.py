import asyncio
import shutil
import threading
import time
import uuid

import git

lock = threading.Lock()


async def sandbox_queue(state):
    if lock.acquire(blocking=False):
        while True:
            if len(state.available_box) == 0 or state.waiting.empty():
                await asyncio.sleep(1)

            print(f'Available sandboxes: {state.available_box}')
            tasks = []
            while not state.waiting.empty() and len(state.available_box) != 0:
                sandbox_number = state.available_box.pop()
                repo_url = state.waiting.get_nowait().url
                tasks.append(asyncio.to_thread(judge, state, sandbox_number, repo_url))
            await asyncio.gather(*tasks)


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
    return {'status': 'judged'}
