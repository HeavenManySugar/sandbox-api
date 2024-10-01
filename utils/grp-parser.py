import json
import sys

from art import text2art


class grp_parser:
    def __init__(self, path):
        self.path = path
        self.data = self.load()

    def load(self):
        with open(self.path, 'r') as f:
            return json.load(f)

    def parser(self, color=False):
        def colorize(statusOK=True, text=''):
            if color:
                return f'\033[{32 if statusOK else 31}m{text}\033[0m'
            return text

        testsuites = self.data['testsuites']
        total_tests_count = 0
        passed_tests = []
        failures_tests = []
        result = (
            text2art('NTUT-OOPOJ', font='lildevil') + '\n'
            f'{colorize(text="[==========]")} Running {self.data["tests"]} tests from '
            f'{len(testsuites)} test suites.\n'
            f'{colorize(text="[----------]")} Global test environment set-up.\n'
        )
        for testsuite in testsuites:
            total_tests_count += len(testsuite['testsuite'])
            result += (
                f'{colorize(text="[----------]")} {len(testsuite["testsuite"])} tests from'
                f' {testsuite["name"]}\n'
            )
            for testcase in testsuite['testsuite']:
                status = f'[ {testcase["status"]:8} ]'
                result += f'{colorize(text=status)} {testcase["name"]}\n'
                if 'failures' not in testcase:
                    result += (
                        f'{colorize(text="[       OK ]")} {testcase["name"]} ({testcase["time"]})\n'
                    )
                    passed_tests.append(testcase['name'])
                else:
                    for failure in testcase['failures']:
                        result += failure['failure'] + '\n'
                    result += (
                        f'{colorize(statusOK=False, text="[  FAILED  ]")} {testcase["name"]}\n'
                    )
                    failures_tests.append(testcase['name'])
            result += (
                f'{colorize(text="[----------]")} {len(testsuite["testsuite"])} tests from'
                f' {testsuite["name"]} (0 ms total)\n\n'
            )

        result += (
            f'{colorize(text="[----------]")} Global test environment tear-down\n'
            f'{colorize(text="[==========]")} Running {total_tests_count} tests from'
            f' {len(testsuites)} test suites.\n'
            f'{colorize(text="[  PASSED  ]")} {len(passed_tests)} tests.\n'
        )
        if failures_tests:
            result += (
                f'{colorize(statusOK=False, text="[  FAILED  ]")} {len(failures_tests)} tests'
                f', listed below:\n'
            )
            for failed_test in failures_tests:
                result += f'{colorize(statusOK=False, text="[  FAILED  ]")} {failed_test}\n'
            result += f'\n{len(failures_tests)} FAILED TESTS\n'
        result += text2art(f'Score: {100*(len(passed_tests)/total_tests_count):.2f}', font='doom')
        return result


if __name__ == '__main__':
    parser = grp_parser(sys.argv[1])
    print(parser.parser(color=True))
