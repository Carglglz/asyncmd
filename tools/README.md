
### aiostats.py


### logging

* ursyslogger.py

Enable remote logging in `/etc/rsyslog.conf`
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


### logging_handlers
