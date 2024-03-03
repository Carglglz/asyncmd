### dotenv files

Use a `.env` dotenv file to set environment variables that can be retrieved with `aioctl.getenv`

```
HOSTNAME=mydevice
LOGLEVEL=DEBUG
LED_PIN=2
AIOREPL=False
```
To check run 

```
$ micropython dotenv.py
{'LED_PIN': 2, 'AIOREPL': False, 'HOSTNAME': 'mydevice', 'LOGLEVEL': 'DEBUG'}
```
