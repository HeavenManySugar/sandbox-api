import queue
import shutil
import subprocess
import threading

import git
from dotenv import dotenv_values
from fastapi import BackgroundTasks
from fastapi.datastructures import State

from ..models.sandbox_model import submission
from ..utils.grp_parser import grp_parser
from ..utils.isolate import sandbox, sandbox_result


class JudgeSystem:
    def __init__(self, state: State):
        self.__lock = threading.Lock()

        self.__state = state
        self.__judging = {}
        self.__waiting = queue.Queue()

    def get_waiting_length(self):
        return len(self.__waiting.queue)

    def get_judging_length(self):
        return len(self.__judging)

    def add_task(self, background_tasks: BackgroundTasks, task: submission):
        if len(self.__state.available_box) == 0:
            self.__waiting.put_nowait(task)
            return 1
        else:
            sandbox_number = self.__state.available_box.pop()
            background_tasks.add_task(self.judge, sandbox_number, task)
            return 0

    def check_available(self):
        if self.__lock.acquire(blocking=True):
            print('Checking available box')
            if len(self.__state.available_box) == 0 or self.__waiting.empty():
                return
            next_task = self.__waiting.get_nowait()
            next_box = self.__state.available_box.pop()
            self.__lock.release()
            self.judge(next_box, next_task)

    def judge(self, box_id: int, task: submission):
        def end_judging(repo_folder):
            # shutil.rmtree(repo_folder, ignore_errors=True)
            self.__judging[box_id] = None
            self.__state.available_box.add(box_id)
            print(f'remain {len(self.__waiting.queue)} tasks')
            self.check_available()

        print(f'Judging {task.url} in sandbox {box_id}')
        self.__judging[box_id] = task.url

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
