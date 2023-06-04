import aioctl
from aioclass import Service
import unittest
import sys
import os
from binascii import hexlify
import re
import hashlib
import uasyncio as asyncio
import gc


class UnittestService(Service):
    _PASS = "[\033[92mPASS\x1b[0m]"
    _FAIL = "[\u001b[31;1mFAIL\u001b[0m]"
    _CHECK = "[\033[92m\u2714\x1b[0m]"
    _XF = "[\u001b[31;1m\u2718\u001b[0m]"

    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"Unittest Service v{self.version}"
        self.type = "schedule.service"
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = []
        self.kwargs = {"testdir": "tests", "modules": ["./lib"], "debug": False}
        self.schedule = {"start_in": 20, "repeat": 60}
        self.tests = []
        self.modules = []
        self._pmodules = {}
        self._cmodules = {}
        self._ptests = {}
        self._ctests = {}
        self.result = unittest.TestResult()
        self.test_result = {}
        self._testsRun = 0
        self._errorsNum = 0
        self._failuresNum = 0
        self.debug = False
        self.log = None

    def __call__(self, stream=sys.stdout):
        for test_file, test in self.test_result.items():
            if test.wasSuccessful():
                print(
                    f"[{self.name}.service] {test_file}: "
                    + f"OK {self._CHECK} @ run: {test.testsRun} ",
                    file=stream,
                )

            else:
                print(
                    f"[{self.name}.service] {test_file}: "
                    + f"{test.failuresNum} tests FAILED {self._XF}"
                    + f" @ run: {test.testsRun}, errors: {test.errorsNum}"
                    + f", failures: {test.failuresNum}",
                    file=stream,
                )

    def show(self):
        return (
            "Stats",
            f"Run: {self._testsRun}, Errors: {self._errorsNum}"
            + f", Failures: {self._failuresNum}",
        )

    def stats(self):
        _stats_tests = {
            "run": self._testsRun,
            "errors": self._errorsNum,
            "failures": self._failuresNum,
            "test": {},
        }
        for test_file, test in self.test_result.items():
            if test.wasSuccessful():
                _stats_tests["test"][test_file] = {"status": "OK", "run": test.testsRun}

            else:
                _stats_tests["test"][test_file] = {
                    "status": "FAIL",
                    "run": test.testsRun,
                    "errors": test.errorsNum,
                    "failures": test.failuresNum,
                }
        return _stats_tests

    def report(self, stream=sys.stdout):
        self.__call__(stream=stream)

        for test_file, test in self.test_result.items():
            self.printErrorList(test.errors, file=stream)
            self.printErrorList(test.failures, file=stream)

    def printErrorList(self, lst, file=sys.stdout):
        sep = "----------------------------------------------------------------------"
        for c, e in lst:
            detail = " ".join((str(i) for i in c))
            print(
                "===================================================================",
                file=file,
            )
            print(f"FAIL: {detail}", file=file)
            print(sep, file=file)
            print(e, file=file)

    def mod_match(self, patt, test):
        if "/" in patt:
            rdir, patt = patt.rsplit("/", 1)
            if patt == "__init__.py" or patt == "__init__.mpy":
                rdir, patt = rdir.rsplit("/", 1)
        patt = patt.replace(".py", "").replace(".mpy", "")
        patt = f"*{patt}*"
        pattrn = re.compile(patt.replace(".", r"\.").replace("*", ".*") + "$")
        try:
            return pattrn.match(test)
        except Exception:
            return False

    def match_mod_test(self, mod, tests):
        return {t: s for t, s in tests.items() if self.mod_match(mod, t)}

    def pair_mods_tests(self):
        for mod in self._cmodules:
            self._cmodules[mod]["tests"] = self.match_mod_test(mod, self._ctests)
            self._cmodules[mod]["tests"].update(
                **self.match_mod_test(mod, self._ptests)
            )
            if not self._cmodules[mod]["tests"]:
                self.modules.remove(mod)
        for mod, tests in self._cmodules.items():
            if tests["tests"]:
                for test in tests["tests"]:
                    if test not in self._ctests:
                        self._ctests[test] = tests["tests"][test]

    def shasum(self, file):
        if os.stat(file)[0] & 0x4000:
            for rfile in os.listdir(file):
                self.shasum(f"{file}/{rfile}")
        else:
            if file.endswith(".py") or file.endswith(".mpy"):
                _hash = hashlib.sha256()
                with open(file, "rb") as bfile:
                    buff = bfile.read(1)
                    _hash.update(buff)
                    while buff != b"":
                        try:
                            buff = bfile.read(256)
                            if buff != b"":
                                _hash.update(buff)
                        except Exception:
                            break
                _result = _hash.digest()
                result = hexlify(_result).decode()
                if self.debug:
                    print(f"{file}: {result}")
                if file.startswith("test_") or "test_" in file:
                    if file not in self.tests:
                        self.tests.append(file)
                    if file not in self._ptests:
                        self._ctests[file] = result
                    else:
                        if self._ptests[file] != result:
                            self._ctests[file] = result
                        else:
                            if file in self._ctests:
                                self._ctests.pop(file)
                else:
                    if file not in self.modules:
                        self.modules.append(file)
                    if file not in self._pmodules:
                        self._cmodules[file] = {
                            "sha": result,
                            "tests": None,
                        }
                    else:
                        if self._pmodules[file]["sha"] != result:
                            self._cmodules[file] = {"sha": result, "tests": None}
                        else:
                            if file in self._cmodules:
                                self._cmodules.pop(file)

    def runtests(self):
        self.pair_mods_tests()
        for mod in self._cmodules:
            self._pmodules[mod] = self._cmodules[mod]
            if "/" in mod:
                rdir, mod = mod.rsplit("/", 1)
                if rdir not in sys.path:
                    sys.path.append(f"./{rdir}")
            mod = mod.replace(".py", "").replace(".mpy", "")
            if mod in sys.modules:
                sys.modules.pop(mod)
                gc.collect()
        if self._ctests:
            self.result = unittest.TestResult()
        for test in self._ctests:
            ab_test = test
            self.test_result[ab_test] = None
            self._ptests[test] = self._ctests[test]
            if "/" in test:
                rdir, test = test.rsplit("/", 1)
                test = test.replace(".py", "").replace(".mpy", "")
                if rdir not in sys.path:
                    sys.path.append(f"./{rdir}")
            if test in sys.modules:
                sys.modules.pop(test)
                gc.collect()

            self.test_result[ab_test] = unittest.main(test)
            if test in sys.modules:
                sys.modules.pop(test)
                gc.collect()
            self.result += self.test_result[ab_test]

    @aioctl.aiotask
    async def task(self, testdir=None, modules=None, debug=False, log=None):
        await asyncio.sleep(2)
        self.debug = debug
        self.log = log
        if testdir:
            if testdir not in sys.path:
                sys.path.append(testdir)
            if log:
                self.log.info(f"[{self.name}.service] Checking tests...")
            self.shasum(testdir)
            if modules:
                if isinstance(modules, list):
                    for mod in modules:
                        self.shasum(mod)
                else:
                    self.shasum(modules)
            self.runtests()

            if log:
                await asyncio.sleep_ms(100)
                if self._ctests:
                    self._testsRun = 0
                    self._errorsNum = 0
                    self._failuresNum = 0
                    self.log.info(
                        f"[{self.name}.service] Ran {len(self._ctests)}"
                        + f" test files --> Total {self.result.testsRun} tests"
                    )

                    if self.result.wasSuccessful():
                        if self.log:
                            self.log.info(
                                f"[{self.name}.service] Tests OK {self._CHECK}"
                            )
                    else:
                        self.log.info(
                            f"[{self.name}.service] {self.result.failuresNum}"
                            + f" tests FAILED {self._XF}"
                        )

                    for test_file, test in self.test_result.items():
                        self._testsRun += test.testsRun
                        self._errorsNum += test.errorsNum
                        self._failuresNum += test.failuresNum
                        if test.wasSuccessful():
                            if self.log:
                                self.log.info(
                                    f"[{self.name}.service] {test_file}: "
                                    + f"OK {self._CHECK}"
                                )
                        else:
                            if self.log:
                                self.log.info(
                                    f"[{self.name}.service] {test_file}: "
                                    + f"{test.failuresNum} FAILED {self._XF}"
                                )
                        await asyncio.sleep_ms(100)
                else:
                    self.log.info(f"[{self.name}.service] Tests up to date")

                if all(t.wasSuccessful() for t in self.test_result.values()):
                    return self._PASS
                else:
                    return self._FAIL


service = UnittestService("unittest")
