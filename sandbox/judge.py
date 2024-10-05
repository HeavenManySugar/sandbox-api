import shutil
import subprocess
import threading

import git
from dotenv import dotenv_values

from ..models.sandbox_model import submission
from ..utils.grp_parser import grp_parser
from ..utils.isolate import sandbox, sandbox_result

lock = threading.Lock()


def check_available(state):
    if lock.acquire(blocking=True):
        print('Checking available box')
        if len(state.available_box) == 0 or state.waiting.empty():
            return
        next_task = state.waiting.get_nowait()
        lock.release()
        judge(state, state.available_box.pop(), next_task)


def judge(state, box_id: int, task: submission):
    def end_judging(repo_folder):
        # shutil.rmtree(repo_folder, ignore_errors=True)
        state.judging[box_id] = None
        state.available_box.add(box_id)
        check_available(state)

    print(f'Judging {task.url} in sandbox {box_id}')
    state.judging[box_id] = task.url

    repo_name = task.uuid
    repo_folder = f'/var/local/lib/isolate/{box_id}/box/{repo_name}'
    internal_folder = f'./{repo_name}'
    try:
        git.Repo.clone_from(task.url, repo_folder)
    except git.exc.GitCommandError as e:
        end_judging(repo_folder)
        print({'status': 'error', 'message': str(e.stderr).split('\n')[2]})
        return
    # do some judging
    box = sandbox(box_id, dotenv_values('.env')['ENABLE_CGROUP'] == 'True')
    subprocess.run(['cp', './scripts/test.sh', f'{repo_folder}/scripts/test.sh'])

    result_script: sandbox_result = box.run(
        [f'{internal_folder}/scripts/test.sh', internal_folder, 'ut_all']
    )
    print(result_script)
    # 這裡未來可以用utils.grp_parser.parse()來解析結果
    # subprocess.run(['./scripts/report.sh', f'{repo_folder}/grp', 'ut_all'])
    grp = grp_parser(f'{repo_folder}/grp/ut_all.json')
    print(grp.parser(color=True))
    print(f'Judged {task.url} in sandbox {box_id} score: {grp.get_score()}')
    end_judging(repo_folder)
    return {'status': 'judged'}
