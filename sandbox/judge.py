import json
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
from ..utils.isolate import read_meta_data, sandbox, sandbox_result


class JudgeSystem:
    def __init__(self, state: State):
        self.__lock = threading.Lock()

        self.__state = state
        self.__judging = {}
        self.__waiting = queue.Queue()

    def get_waiting_length(self):
        return len(self.__waiting.queue)

    def get_judging_length(self):
        return len(list(filter(None, self.__judging.values())))

    def add_task(self, background_tasks: BackgroundTasks, task: submission):
        g = git.cmd.Git()
        try:
            ls_remote = g.ls_remote(task.url)
            if not ls_remote:
                return 2
        except git.exc.GitCommandError:
            return 2

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
                self.__lock.release()
                return
            next_task = self.__waiting.get_nowait()
            next_box = self.__state.available_box.pop()
            self.__lock.release()
            self.judge(next_box, next_task)

    def judge(self, box_id: int, task: submission):
        def end_judging(repo_folder):
            shutil.rmtree(repo_folder, ignore_errors=True)
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
        box = sandbox(repo_name, box_id, dotenv_values('.env')['ENABLE_CGROUP'] == 'True')
        subprocess.run(['cp', './scripts/test.sh', f'{repo_folder}/scripts/test.sh'])

        result_script: sandbox_result = box.run(
            [f'{internal_folder}/scripts/test.sh', internal_folder, 'ut_all']
        )
        try:
            with open(f'./result/{repo_name}/result_script.txt', 'w') as f:
                f.write(f'{result_script}')
            if result_script.meta['exitcode'] != 0:
                print(f'Judged {task.url} in sandbox {box_id} error: {result_script.stderr}')
                end_judging(repo_folder)
                return
            # 這裡未來可以用utils.grp_parser.parse()來解析結果
            # subprocess.run(['./scripts/report.sh', f'{repo_folder}/grp', 'ut_all'])
            shutil.copy2(f'{repo_folder}/grp/ut_all.json', f'./result/{repo_name}/grp.json')
            shutil.copy2(f'{repo_folder}/valgrind/ut_all.log', f'./result/{repo_name}/valgrind.log')
            grp = grp_parser(f'{repo_folder}/grp/ut_all.json')
            with open(f'./result/{repo_name}/grp.txt', 'w') as f:
                f.write(grp.parser())
            print(f'Judged {task.url} in sandbox {box_id} score: {grp.get_score()}')
        except FileNotFoundError:
            pass
        end_judging(repo_folder)
        return

    def get_result(self, uuid):
        with open(f'./result/{uuid}/result_script.txt', 'r') as f:
            return f.read()

    def get_valgrind(self, uuid):
        with open(f'./result/{uuid}/valgrind.log', 'r') as f:
            return f.read()

    def get_grp_json(self, uuid):
        with open(f'./result/{uuid}/grp.json', 'r') as f:
            return json.load(f)

    def get_grp_text(self, uuid):
        with open(f'./result/{uuid}/grp.txt', 'r') as f:
            return f.read()

    def get_meta(self, uuid):
        r = json.dumps(read_meta_data(f'./result/{uuid}/meta'))
        return json.loads(r)
