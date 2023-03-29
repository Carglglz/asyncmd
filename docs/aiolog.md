
## Documentation for `aiolog`

`aiolog` provides a special `stream` class with the following features:
- RAM based (`io.StringIO`) circular buffer. This allows to preallocate a certain amount of RAM dedicated 
to logging, and the log will rotate seamlessly when the max size is reached.
- Interactively inspect its content same as using `cat` with `*` wildcard matching.
- Interactively follow its content asynchronously, similarly as using `tail -F`, and also with `*` wildcard matching.
- Can be used with `micropython-lib/python-stdlib/logging` as a stream.


### Usage

The class is `AioStream`, and is easily set up as e.g.
```
streamlog = Aiostream(2000) 

# this is by default included in aiolog, to do e.g. from aiolog import streamlog

```

#### Adding `AioStream` to `aioctl`

Use `aioctl.set_log` as e.g.

```
aioctl.set_log(streamlog)
```

So now the contents can be inspected using `aioctl.log()` or `await
aioctl.follow()`



#### Adding `AioStream` to `micropython` logging

`streamlog` can be added as a stream as e.g.
```python

import logging
import sys
import aioctl
from aiolog import streamlog 

aioctl.set_log(streamlog)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S", # micropython-lib/python-stdlib/time required
    stream=streamlog,
)
log = logging.getLogger(sys.platform) 

```
or if using handlers[^1]

```python
formatter = logging.Formatter("%(asctime)s [%(name)s] [%(levelname)s] %(message)s")
# Stream
stream_handler = logging.StreamHandler(stream=streamlog)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
log.addHandler(stream_handler)
```


#### Log inspection 

e.g.
```
--> aioctl.log()
2023-03-29 12:16:30 [pyboard] [INFO] [hello.service] LED 2 toggled!
2023-03-29 12:16:32 [pyboard] [INFO] [hello.service] LED 2 toggled!
2023-03-29 12:16:34 [pyboard] [INFO] [hello.service] LED 3 toggled!
2023-03-29 12:16:36 [pyboard] [INFO] [hello.service] LED 4 toggled!
2023-03-29 12:16:38 [pyboard] [INFO] [hello.service] LED 1 toggled!
2023-03-29 12:16:40 [pyboard] [INFO] [hello.service] LED 3 toggled!
2023-03-29 12:16:42 [pyboard] [INFO] [hello.service] LED 4 toggled!
2023-03-29 12:16:44 [pyboard] [INFO] [hello.service] LED 4 toggled!
2023-03-29 12:16:44 [pyboard] [ERROR] [hello.service] ZeroDivisionError: divide by zero
2023-03-29 12:16:45 [pyboard] [ERROR] [hello.service] Error callback divide by zero
2023-03-29 12:17:11 [pyboard] [INFO] [watcher.service] Error @ Task hello.service ZeroDivisionError: divide by zero
2023-03-29 12:17:11 [pyboard] [INFO] [watcher.service] Restarting Task hello.service
2023-03-29 12:17:11 [pyboard] [INFO] [hello.service] LED 3 toggled!
2023-03-29 12:17:13 [pyboard] [INFO] [hello.service] LED 1 toggled!
2023-03-29 12:17:15 [pyboard] [INFO] [hello.service] LED 4 toggled!
2023-03-29 12:17:17 [pyboard] [INFO] [hello.service] LED 2 toggled!
--> 
```

[^1]: Check out `logging_handlers` directory for custom handlers too .e.g
    `FileRotationHandler`  
