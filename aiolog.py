import io
import re
import asyncio


class AioStream(io.StringIO):
    def __init__(self, alloc_size):
        super().__init__(alloc_size)
        self._max_size = alloc_size
        self._write = super().write
        self._tmp = io.StringIO(100)
        self._lw = 0
        self._comp = False

    def write(self, sdata):
        if sdata.endswith("\n"):
            if self.tell() + len(sdata) + self._tmp.tell() >= self._max_size:
                # clean
                self._write(" " * ((self._max_size - self.tell()) - 1))
                self._write("\n")
                # rotate
                self.seek(0)
                self._comp = True
            self._tmp.seek(0)
            self._write(self._tmp.read(self._lw))
            self._tmp.seek(0)
            self._write(sdata)
        else:
            self._lw = self._tmp.write(sdata)

    def cat(self, grep=""):
        index = self.tell()
        if self._comp:
            self.readline()
        if grep:
            for line in self:
                if (
                    line
                    and ("*" in grep or isinstance(grep, list))
                    and self._grep(grep, line)
                ):
                    print(line, end="")
                elif isinstance(grep, str):
                    if grep in line:
                        print(line, end="")
        else:
            for line in self:
                if line.strip():
                    print(line, end="")

        self.seek(0)
        # read and grep for regex
        if grep:
            for line in self:
                if (
                    line
                    and ("*" in grep or isinstance(grep, list))
                    and self._grep(grep, line)
                ):
                    print(line, end="")

                elif isinstance(grep, str):
                    if grep in line:
                        print(line, end="")
                if self.tell() >= index:
                    self.seek(index)
                    return
        else:
            for line in self:
                if line.strip():
                    print(line, end="")
                if self.tell() >= index:
                    self.seek(index)
                    return
        self.seek(index)

    def _grep(self, patt, line):
        if isinstance(patt, list):
            pass
        else:
            patt = [patt]
        _pattlst = (
            re.compile(_patt.replace(".", r"\.").replace("*", ".*") + "$")
            for _patt in patt
        )
        try:
            return any(_pattrn.match(line) for _pattrn in _pattlst)
        except Exception:
            return None

    async def follow(self, grep="", wait=0.05):
        init_index = self.tell()
        while True:
            try:
                current_index = self.tell()
                if current_index != init_index:
                    self.seek(init_index)
                    if grep:
                        if "*" not in grep:
                            for line in self:
                                if line and grep in line:
                                    print(line, end="")

                                if self.tell() == current_index:
                                    break
                            if current_index < init_index:
                                self.seek(0)
                                init_index = 0
                                for line in self:
                                    if line and grep in line:
                                        print(line, end="")

                                    if self.tell() == current_index:
                                        break

                        else:
                            for line in self:
                                if line and self._grep(grep, line):
                                    print(line, end="")

                                if self.tell() == current_index:
                                    break

                            if current_index < init_index:
                                self.seek(0)
                                init_index = 0
                                for line in self:
                                    if line and self._grep(grep, line):
                                        print(line, end="")

                                    if self.tell() == current_index:
                                        break

                    else:
                        for line in self:
                            if line.strip():
                                print(line, end="")

                            if self.tell() == current_index:
                                break

                        if current_index < init_index:
                            self.seek(0)
                            init_index = 0
                            for line in self:
                                if line.strip():
                                    print(line, end="")

                                if self.tell() == current_index:
                                    break

                init_index = current_index
                await asyncio.sleep(wait)
            except KeyboardInterrupt:
                break


streamlog = AioStream(2000)
