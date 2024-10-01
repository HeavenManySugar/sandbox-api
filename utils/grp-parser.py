import json
import sys
from enum import Enum

from art import text2art


class ScoreMethod(Enum):
    SUITE = 1
    TEST = 2


class grp_parser:
    def __init__(self, path):
        self.path = path
        self.data = self.load()
        self.scoremethod: ScoreMethod = ScoreMethod.TEST
        self.calculate_score()

    def calculate_score(self):
        testsuites = self.data['testsuites']
        self.total_tests_count = 0
        self.passed_tests = []
        self.failures_tests = []
        self.failures_suites = set()
        for testsuite in testsuites:
            self.total_tests_count += len(testsuite['testsuite'])
            for testcase in testsuite['testsuite']:
                if 'failures' not in testcase:
                    self.passed_tests.append(testcase['name'])
                else:
                    self.failures_tests.append(testcase['name'])
                    self.failures_suites.add(testsuite['name'])
        if self.scoremethod == ScoreMethod.SUITE:
            self.score = 100 * (1 - len(self.failures_suites) / len(testsuites))
        elif self.scoremethod == ScoreMethod.TEST:
            self.score = 100 * (len(self.passed_tests) / self.total_tests_count)

    def load(self):
        with open(self.path, 'r') as f:
            return json.load(f)

    def parser(self, color=False):
        def colorize(statusOK=True, text=''):
            if color:
                return f'\033[{32 if statusOK else 31}m{text}\033[0m'
            return text

        testsuites = self.data['testsuites']
        result = (
            text2art('NTUT-OOPOJ', font='lildevil') + '\n'
            f'{colorize(text="[==========]")} Running {self.data["tests"]} tests from '
            f'{len(testsuites)} test suites.\n'
            f'{colorize(text="[----------]")} Global test environment set-up.\n'
        )
        for testsuite in testsuites:
            result += (
                f'{colorize(text="[----------]")} {len(testsuite["testsuite"])} tests from'
                f' {testsuite["name"]}'
            )
            if self.scoremethod == ScoreMethod.SUITE:
                result += f'({100*(1/len(testsuites)):.1f}pt)'
            elif self.scoremethod == ScoreMethod.TEST:
                result += f'({100*(len(testsuite["testsuite"])/self.total_tests_count):.1f}pt)'
            result += '\n'
            for testcase in testsuite['testsuite']:
                status = f'[ {testcase["status"]:8} ]'
                result += f'{colorize(text=status)} {testcase["name"]}'
                if self.scoremethod == ScoreMethod.TEST:
                    result += f'({100*(1/self.total_tests_count):.1f}pt)'
                result += '\n'
                if 'failures' not in testcase:
                    result += (
                        f'{colorize(text="[       OK ]")} {testcase["name"]} ({testcase["time"]})\n'
                    )
                else:
                    for failure in testcase['failures']:
                        result += failure['failure'] + '\n'
                    result += (
                        f'{colorize(statusOK=False, text="[  FAILED  ]")} {testcase["name"]}\n'
                    )
            result += (
                f'{colorize(text="[----------]")} {len(testsuite["testsuite"])} tests from'
                f' {testsuite["name"]} (0 ms total)\n\n'
            )

        result += (
            f'{colorize(text="[----------]")} Global test environment tear-down\n'
            f'{colorize(text="[==========]")} Running {self.total_tests_count} tests from'
            f' {len(testsuites)} test suites.\n'
            f'{colorize(text="[  PASSED  ]")} {len(self.passed_tests)} tests.\n'
        )
        if self.failures_tests:
            result += (
                f'{colorize(statusOK=False, text="[  FAILED  ]")} {len(self.failures_tests)} tests'
                f', listed below:\n'
            )
            for failed_test in self.failures_tests:
                result += f'{colorize(statusOK=False, text="[  FAILED  ]")} {failed_test}\n'
            result += f'\n{len(self.failures_tests)} FAILED TESTS\n'
        result += text2art(f'Score: {self.score:.1f}', font='doom')
        return result


if __name__ == '__main__':
    parser = grp_parser(sys.argv[1])
    print(parser.parser(color=True))
