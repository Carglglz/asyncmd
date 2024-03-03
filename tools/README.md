
## aiostats

* aiostats.py

Set of tools to get stats about `aiotasks` and/or `aioservices`.

```py
 display(taskm="*") : function

 stats(taskm="*", debug=False, traceback=None) : function

 task_status(name) : function

 logtail(grep="", log=aioctl._AIOCTL_LOG) : function

 pipefile(client, topic, file) : function  # client is an async_mqtt client

 pipelog(client, topic, from_idx=None, log=aioctl._AIOCTL_LOG) : function

```

## config 

A `dotenv.py` tool to write and parse *dotenv* files see [api](config/README.md)

## logging

#### ServiceLogger

A custom logger class in `service_logger.py` to be used in `aioservices`.

#### HeartBeat
* `ledhb.py`
* `buzzhb.py`

`HeartBeat` led and buzzer classes to use with `HeartBeatHandler`.

#### Remote logging
* [ursyslogger.py](./logging/ursyslogger.py)

Enable remote [^1] logging in `/etc/rsyslog.conf`
```
# provides TCP syslog reception
module(load="imtcp")
input(type="imtcp" port="514")

# Remote logs
# $template RemoteLogs,"/var/log/%HOSTNAME%/%PROGRAMNAME%.log"
#*.* ?RemoteLogs
#& stop
$template remote-incoming-logs, "/var/log/remote/%HOSTNAME%.log"
*.* ?remote-incoming-logs

```


## logging_handlers


### FileRotationHandler

* filehandler.py

The `FileRotationHandler` logs messages to a file. The file path can be
specified using the `filename` parameter, and the `max_size` parameter
indicates the file maximum size in bytes before the log is rotated. Currently
log rotation only allows two files at any given time .i.e the current log and
the previous log indicated with `<filename>.1`. This handler is useful for
debugging errors, so setting handler level to `logging.ERROR` is the best option.

### HeartBeatHandler (hardware)

* hbhandler.py

The `HeartBeatHandler` use the log level for physical debugging using hardware
devices such as a buzzer or LED. A `<Device>HeartBeat` object from any
`tools/logging/<device>hb.py` is expected as the first argument. This handler
is useful for monitoring the system's heartbeat .e.g with `logging.INFO` level
and detecting potential problems with `logging.WARNING` or `logging.ERROR`.


### RsyslogHandler

* rsysloghandler.py

The `RsyslogHandler` logs messages to an external log server using the Rsyslog
protocol. It expects a `Rsyslogger` object from `tools/logging/ursyslogger.py`
as the first argument. This handler is useful for sending logs to a centralized
logging system or for integration with other systems that use Rsyslog.
The `RsyslogHandler` can be enabled in `network.service` with option `"rsyslog": "<hostname>"`
where `<hostname>` is the hostname of the remote server. (see [remote logging](#remote-logging))



[^1]: See [rsyslog](https://www.rsyslog.com/receiving-messages-from-a-remote-system) documentation 
