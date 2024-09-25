import re
import subprocess


def init_sandbox(box_id: int, cg: bool = False):
    cg_setting = ('--cg',) if cg else ()
    return subprocess.run(
        ['isolate', '--init', '-b', str(box_id), *cg_setting], capture_output=True
    )


def cleanup_sandbox(box_id: int, cg: bool = False):
    cg_setting = ('--cg',) if cg else ()
    return subprocess.run(
        ['isolate', '--cleanup', '-b', str(box_id), *cg_setting], capture_output=True
    )


def read_meta_data(file_path: str):
    with open(file_path) as file:
        content = file.read()
    pattern = re.compile(r'([\w-]+):([\d.]+)')
    matches = pattern.findall(content)
    data = {key: float(value) if '.' in value else int(value) for key, value in matches}
    return meta_data(data)


class meta_data:
    def __init__(self, meta: dict):
        self.cg_mem = meta.get('cg-mem', None)
        self.cg_oom_killed = meta.get('cg-oom-killed', None)
        self.csw_forced = meta.get('csw-forced', None)
        self.csw_voluntary = meta.get('csw-voluntary', None)
        self.exitcode = meta.get('exitcode', '1')
        self.exitsig = meta.get('exitsig', None)
        self.killed = meta.get('killed', None)
        self.max_rss = meta.get('max-rss', None)
        self.message = meta.get('message', None)
        self.status = meta.get('status', None)
        self.time = meta.get('time', None)
        self.time_wall = meta.get('time-wall', None)

    def __str__(self):
        return f'cg_mem: {self.cg_mem}\ncg_oom_killed: {self.cg_oom_killed}\n\
csw_forced: {self.csw_forced}\ncsw_voluntary: {self.csw_voluntary}\nexitcode: {self.exitcode}\n\
exitsig: {self.exitsig}\nkilled: {self.killed}\nmax_rss: {self.max_rss}\nmessage: {self.message}\n\
status: {self.status}\ntime: {self.time}\ntime_wall: {self.time_wall}'


class sandbox_result:
    def __init__(self, meta: meta_data, stdout: bytes, stderr: bytes):
        self.meta = meta
        self.stdout = stdout.strip()
        self.stderr = stderr.strip()

    def __str__(self):
        return f'stdout: {self.stdout}\nstderr: {self.stderr}'


class sandbox:
    def __init__(self, box_id: int, cg: bool = False):
        self.box_id = box_id
        self.cwd = f'/var/local/lib/isolate/{box_id}/box'
        self.cg = cg

    def run(self, command: list, timeout: int, mem_kb: int = 256262144):
        mem_setting = ('--mem', str(mem_kb)) + (('--cg-mem', str(mem_kb)) if self.cg else ())
        cg_setting = ('--cg',) if self.cg else ()
        print(mem_setting)
        try:
            r = subprocess.run(
                [
                    'isolate',
                    '--box-id',
                    str(self.box_id),
                    '--processes',
                    '--full-env',
                    '--run',
                    '--time',
                    str(timeout),
                    '--meta',
                    self.cwd + '/meta',
                    *mem_setting,
                    *cg_setting,
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
            print(meta)
            return sandbox_result(meta, r.stdout, r.stderr)
        except subprocess.TimeoutExpired:
            return sandbox_result(1, '', 'Time Limit Exceeded')
        except subprocess.CalledProcessError as e:
            return sandbox_result(e.returncode, e.stdout, e.stderr)
