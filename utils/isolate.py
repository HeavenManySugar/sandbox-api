import os
import re
import shutil
import subprocess
from typing import Optional
from uuid import UUID


def init_sandbox(box_id: int, cg: bool = False):
    cg_setting = ('--cg',) if cg else ()
    return subprocess.run(
        ['isolate', '--init', '-b', str(box_id), *cg_setting], capture_output=True, text=True
    )


def cleanup_sandbox(box_id: int, cg: bool = False):
    cg_setting = ('--cg',) if cg else ()
    return subprocess.run(
        ['isolate', '--cleanup', '-b', str(box_id), *cg_setting], capture_output=True, text=True
    )


def read_meta_data(file_path: str) -> dict:
    with open(file_path) as file:
        content = file.read()
    pattern = re.compile(r'([\w-]+):([\d.]+)')
    matches = pattern.findall(content)
    data = {key: float(value) if '.' in value else int(value) for key, value in matches}
    return data


class sandbox_result:
    def __init__(self, meta: dict, stdout: bytes, stderr: bytes):
        self.meta = meta
        self.stdout = stdout.strip()
        self.stderr = stderr.strip()

    def __str__(self):
        return f'stdout: {self.stdout}\nstderr: {self.stderr}'


class sandbox:
    def __init__(self, repo_name: UUID, box_id: int, cg: bool = False):
        self.repo_name = repo_name
        self.box_id = box_id
        self.cwd = f'/var/local/lib/isolate/{box_id}/box'
        self.cg = cg

    def run(self, command: list, timeout: Optional[int] = None, mem_kb: Optional[int] = None):
        mem_setting = ()
        if mem_kb:
            mem_setting = ('--mem', str(mem_kb)) + (('--cg-mem', str(mem_kb)) if self.cg else ())
        cg_setting = ('--cg',) if self.cg else ()
        timeout_setting = ('--time', str(timeout)) if timeout else ()
        try:
            r = subprocess.run(
                [
                    'isolate',
                    '--box-id',
                    str(self.box_id),
                    '--processes',
                    '--full-env',
                    '--run',
                    '--meta',
                    self.cwd + '/meta',
                    *mem_setting,
                    *cg_setting,
                    *timeout_setting,
                    '--',
                    *command,
                ],
                cwd=self.cwd,
                timeout=timeout,
                capture_output=True,
                text=True,
            )
            # read meta data
            meta = read_meta_data(self.cwd + '/meta')
            if not os.path.exists(f'./result/{self.repo_name}'):
                os.makedirs(f'./result/{self.repo_name}')

            shutil.copy(f'{self.cwd}/meta', f'./result/{self.repo_name}/meta')
            # print(meta)
            return sandbox_result(meta, r.stdout, r.stderr)
        except subprocess.TimeoutExpired:
            return sandbox_result(1, '', 'Time Limit Exceeded')
        except subprocess.CalledProcessError as e:
            return sandbox_result(e.returncode, e.stdout, e.stderr)
