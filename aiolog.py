import io
import re
import uasyncio as asyncio


class AioStream(io.StringIO):
    def __init__(self, alloc_size):
        super().__init__(alloc_size)
        self._max_size = alloc_size
        self._write = super().write

    def write(self, sdata):
        if self.tell() + len(sdata) > self._max_size:
            self.seek(0)
        self._write(sdata)

    def cat(self, grep=""):
        index = self.tell()
        self.seek(0)
        # read and grep for regex
        if grep:
            for line in self:
                if line and "*" in grep and self._grep(grep, line):
                    print(line, end="")
                elif grep in line:
                    print(line, end="")
                if self.tell() >= index:
                    self.seek(index)
                    return
        else:
            for line in self:
                print(line, end="")
                if self.tell() >= index:
                    self.seek(index)
                    return
        self.seek(index)

    def _grep(self, patt, line):
        pattrn = re.compile(patt.replace(".", r"\.").replace("*", ".*") + "$")
        try:
            return pattrn.match(line)
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
                            if line:
                                print(line, end="")

                            if self.tell() == current_index:
                                break

                        if current_index < init_index:
                            self.seek(0)
                            init_index = 0
                            for line in self:
                                if line:
                                    print(line, end="")

                                if self.tell() == current_index:
                                    break

                init_index = current_index
                await asyncio.sleep(wait)
            except KeyboardInterrupt:
                break


streamlog = AioStream(2000)
