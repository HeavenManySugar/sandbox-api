# 轉換googletest的xml格式為json格式

import json
import xml.etree.ElementTree as ET


class TestCase:
    def __init__(self, name: str, status: str, result: str, time: float, classname: str):
        self.name = name
        self.status = status
        self.result = result
        self.time = time
        self.classname = classname


class GoogleTest:
    def __init__(self, xml_file):
        self.xml_file = xml_file
        self.test_cases = self.parse_gtest_xml()

    def parse_gtest_xml(self):
        tree = ET.parse(self.xml_file)
        root = tree.getroot()
        test_cases = []
        for testsuite in root:
            print(testsuite.attrib)
            for testcase in testsuite:
                test_case = TestCase(
                    name=testcase.attrib['name'],
                    status=testcase.attrib['status'],
                    result=testcase.attrib['result'],
                    time=float(testcase.attrib['time']),
                    classname=testcase.attrib['classname'],
                )
                test_cases.append(test_case)
        return test_cases

    def to_json(self):
        return json.dumps(self.test_cases)

    def score(self):
        passed = 0
        failed = 0
        for test_case in self.test_cases:
            if test_case['status'] == 'PASSED':
                passed += 1
            else:
                failed += 1
        return {'total': len(self.test_cases), 'passed': passed, 'failed': failed}


GoogleTest('test.xml')
