## GWOApi
Really **cool** module for interacting with gdańskie wydawnictwo oświatowe's apps
> Uses only 3 external packages

```bash
> pip install -U gwo
```

## Usage
```python
import asyncio
from GWO import GWOApi

async def main():
    client: GWOApi = await GWOApi.login("example", "password123")
    print(client.user)

asyncio.run(main())
```

> We use analytics but don't worry, they're anonymous