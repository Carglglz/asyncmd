# Documentation for `aioctl`

`aioctl` provides a simple interface for creating, managing, monitoring and debugging asyncio tasks. This documentation will cover the various functions and methods available in `aioctl`.

## `aioctl.aiotask`

This is a decorator that can be used to define a traceable asyncio task. This decorator adds name and time traceability plus event callbacks in case of the task being cancelled (stopped) or if the task raise an error. e.g.
````
@aioctl.aiotask
async def blink():
....
````

## `aioctl.add()`

This method is used to add a new task to `aioctl` group. It takes the following arguments:

- `coro`: The coroutine function that defines the task.
- `args`: A tuple of arguments to pass to the coroutine function.
- `kwargs`: A dictionary of keyword arguments to pass to the coroutine function.
- `name`: A string that identifies the task.
- `_id`: If set should be the same as `name`, so it can be used to identify the task (used by aiotask)
- `on_stop`: An optional callback function that will be called when the task is stopped.
- `on_error`: An optional callback function that will be called if the task raises an exception.
- `log`: An optional logger object so the task's output can be logged.

## `aioctl.tasks()`

This method returns a list of all the "awaitable" tasks currently managed by `aioctl`.

## `aioctl.status()`

This function returns the status of all tasks managed by `aioctl`. The status can be one of the following:

- `"running"`: The task is currently running. Indicated visually with a green dot
- `"stopped"`: The task has been (cancelled) stopped. Indicated visually with a yellow dot
- `"done"`: The task has completed successfully. Indicated visually with a dot (font color)
- `"error"`: The task has raised an exception.Indicated visually with a red dot
- `"scheduled"`: The task is scheduled to run in the future.Indicated visually with a blue dot
- `"scheduled - done"`: The task completed successfully and will run again in the future. Indicated visually with a blue dot

It also displays tasks state timestamps, and result if any.
If debug mode is enabled, displays args and kwargs too.
If `aioctl` log is set it also shows the log entries with the name of the task (.i.e `cat | grep`).
If the task is scheduled, it shows the schedule (last time, next time, in seconds and formatted time tuple)

It takes the following arguments:

- `name`: Name of the task (accepts `*` wildcard), or None in which case will show all tasks.
- `log`: To show log entries, by default is `True`.
- `debug`: To show args/kwargs, by default is False. Debug mode overrides this if Debug mode is `True`. 


## `aioctl.debug()`

This method toggles debug mode for `aioctl`. When debug mode is enabled, additional information will be displayed.

## `aioctl.group()`

This method returns an instance of an `aioctl` task group. The task group can be used to manage/modify or inspect tasks internals .e.g args/kwargs
or other properties.

## `aioctl.delete()`

This method is used to delete a task from an `aioctl` task group. Accepts a name (with `*` wildcards) and multiple tasks.

## `aioctl.stop()`

This method is used to stop one or more tasks managed by `aioctl`. Accepts a name (with `*` wildcards) or None, in which case all tasks will be stopped.

## `aioctl.start()`

This method is used to start one or more tasks managed by `aioctl`. Accepts a name (with `*` wildcards) or None, in which case all tasks will be started.


## `aioctl.result()`

This method is used to get the result of one or more tasks managed by `aioctl`. Accepts a name (with `*` wildcards) or None, in which case all tasks results will be displayed.


## `aioctl.traceback()`

This method is used to get the traceback of one or more tasks managed by `aioctl`. Accepts a name (with `*` wildcards) or None, in which case all tasks results containing errors/tracebacks will be displayed.


## `aioctl.set_log()`

This method is used to set the stream log (from `aiolog`) for `aioctl`. This is the stream that contains the tasks output (if any).

## `aioctl.log()`

This method is used to view the stream log. Accepts a name (with `*` wildcards) same as using  `"cat"` or `"cat | grep"` 

## `aioctl.follow()`

This method is used to follow the stream log. Accepts a name (with `*` wildcards) same as using `"tail -F"` or `"grep"`.
This is an async task so to run use `await aioctl.follow()`

See some [examples](https://github.com/Carglglz/asyncmd/tree/main/examples)
