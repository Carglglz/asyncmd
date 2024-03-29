class ServiceException(Exception):
    pass


class Service:
    def __init__(self, name, info="", loaded=True):
        self.name = name
        self.path = ""
        self.info = info
        self.type = "runtime.service"  # continuous running, other types are
        self.docs = ""
        self.enabled = False  # preset
        self.loaded = loaded
        self._child_tasks = set()
        self.log = None
        # core.service --> run one time at boot
        # schedule.service --> run and stop following a schedule

    def __repr__(self):
        return f"Service: {self.name}.service from {self.path}"

    def add_ctask(self, aioctl, ctask, cname, *args, **kwargs):
        if f"{self.name}.service.{cname}" in aioctl.group().tasks:
            aioctl.delete(f"{self.name}.service.{cname}")
        aioctl.add(
            ctask,
            self,
            *args,
            name=f"{self.name}.service.{cname}",
            _id=f"{self.name}.service.{cname}",
            **kwargs,
        )

    def add_logger(self, logger, level="INFO", service_logger=None):
        if not self.log:
            if service_logger:
                try:
                    if service_logger is True:
                        from service_logger import ServiceLogger
                    else:
                        ServiceLogger = __import__(
                            f"{service_logger}", [], [], ["ServiceLogger"]
                        )

                    self.log = ServiceLogger(logger, self.name, level=level)
                except Exception:
                    logger.error(f"[{self.name}] Service logger not available")
                    logger.info(f"[{self.name}] Using default logger")
                    self.log = logger
            else:
                self.log = logger


class PQueue:
    def __init__(self):
        self.services = []
        self.req = {}
        self.core = []
        self.priority_score = {}

    def add(self, *services):
        for service in services:
            self.services.append(service)
            rq = service.kwargs.get("require", [])
            if isinstance(rq, str):
                rq = [rq]
            if not rq:
                self.core.append(service.name)
                continue
            for core_rq in rq:
                if core_rq not in self.req:
                    self.req[core_rq] = [service.name]
                else:
                    self.req[core_rq] += [service.name]

    def get_score(self, serv, score, lev=0, rservs=[]):
        _score = score
        for dep in self.req[serv]:
            if dep not in self.req:
                _score += 1
                # print(f"{lev*' '}{serv} --> {dep}")
            else:
                if serv not in self.req[dep]:
                    if dep not in rservs:
                        rservs.append(dep)

                        # print(f"{lev*' '}{serv} --> {dep} ")
                        lev += 4
                        _score += 1
                        _score += self.get_score(dep, _score, lev, rservs)
                        lev -= 4
                        rservs.remove(dep)
                    else:
                        _score += 1

                else:
                    _score += 1

        return _score

    def resolve(self):
        # 2p for being core(no deps)
        # 1p for every dependency
        # finally
        # if dependency is nested required
        # add those points too.
        for cservice in set(self.core):
            self.priority_score[cservice] = 1

        for _cservice in self.req:
            if _cservice not in self.priority_score:
                self.priority_score[_cservice] = self.get_score(_cservice, 0)
            else:
                score = self.priority_score[_cservice]
                self.priority_score[_cservice] += self.get_score(_cservice, score)

    def psolve(self):
        self.resolve()
        hp = [(k, v) for k, v in self.priority_score.items()]
        hp.sort(key=lambda x: x[1], reverse=True)
        servs_dict = {sv.name: sv for sv in self.services}
        ordered_srvs = [
            servs_dict.get(
                s, Service(s, info=ServiceException("Service Not Found"), loaded=False)
            )
            for s, p in hp
        ]
        lp = {allsrv for allsrv in self.services} - {ords for ords in ordered_srvs}

        return hp, ordered_srvs, list(lp)
