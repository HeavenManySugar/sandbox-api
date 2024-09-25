import shutil

import git
from dotenv import dotenv_values

from ..models.sandbox_model import submission
from ..utils.isolate import sandbox, sandbox_result
from ..utils.cmake import get_cmake_build_command, get_cmake_make_command


def check_available(state):
    if len(state.available_box) == 0 or state.waiting.empty():
        return
    next_task = state.waiting.get_nowait()
    judge(state, state.available_box.pop(), next_task.url, next_task.uuid)


def judge(state, box_id: int, task: submission):
    def end_judging(repo_folder):
        shutil.rmtree(repo_folder, ignore_errors=True)
        state.judging[box_id] = None
        state.available_box.add(box_id)
        check_available(state)

    print(f'Judging {task.url} in sandbox {box_id}')
    state.judging[box_id] = task.url

    repo_name = task.uuid
    repo_folder = f'/var/local/lib/isolate/{box_id}/box/{repo_name}'
    try:
        git.Repo.clone_from(task.url, repo_folder)
    except git.exc.GitCommandError as e:
        end_judging(repo_folder)
        print({'status': 'error', 'message': str(e.stderr).split('\n')[2]})
    # do some judging
    box = sandbox(box_id, dotenv_values('.env')['ENABLE_CGROUP'])
    result_build: sandbox_result = box.run(get_cmake_build_command(repo_folder))
    print(result_build)
    result_make: sandbox_result = box.run(get_cmake_make_command(repo_folder))
    print(result_make)
    end_judging(repo_folder)
    return {'status': 'judged'}
