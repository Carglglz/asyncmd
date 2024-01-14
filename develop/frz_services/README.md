### Freezing services in firmware

To freeze services add the required services in a manifest file (see
`/develop/manifest_develop.py`) and then add the required services from above
to `aioservices/services` in the device, this would allow service discovery but
will load the frozen service instead, .e.g 

`aioservices/services/hello_service.py`

```python
from hello_service import service
```
