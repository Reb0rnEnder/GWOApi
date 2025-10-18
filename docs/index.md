# GWO (Python)
### Reverse-enginered [GWO](https://gwo.pl/) api wrapper for Python
[![PyPI - Version](https://img.shields.io/pypi/v/gwo?color=%2334D058)](https://pypi.org/project/gwo/) [![PyPI Downloads](https://static.pepy.tech/personalized-badge/gwo?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads)](https://pepy.tech/projects/gwo) [![Static Badge](https://img.shields.io/badge/python-3.9_%7C_3.10_%7C_3.11_%7C_3.12_%7C_3.13_%7C_3.14-%2334D058)](https://pypi.org/project/gwo/)
---
GWO (Python) is an api wrapper for GWO (Website) that allows you to programmatically extract excercises from the users accesses, modify and view user info, and anwser exercises all in a simple to use package
### 📱 Ultra compatible
Due to its simple nature GWO (Python) is compatible with almost every platform*
### 🧶 Niche but usefull
* Stuck on an exercise? Code up a tool to show you the anwser.
* Training an ai? Extract all exercises and their anwsers to train a model capable of solving the exercises.
* Idk what else you might wanna use this for, its very niche i said.

## Example of a script using GWO
Below is a simple script, using user input to log in and print out user info:
```python
from GWO import GWOApi, User, LoginException, FetchException
from typing import Optional
import asyncio

async def login(username: str, password: str) -> Optional[User]:
    if not (username and password):
        return None
    try:
        client: GWOApi = await GWOApi.login(username, password)
        return client.user
    except (LoginException, FetchException):
        return None

async def main():
    print("Welcome to GWO!\nLogin with your GWO account")
    while True:
        username: str = input("Username: ")
        password: str = input("Password: ")
        if not (username and password):
            print("Username or password cannot be empty!"); continue
        user: Optional[User] = await login(username, password)
        if not user:
            print("Invalid username or password!"); continue
        print(f"Hello, {user.firstName}!"); break

asyncio.run(main())
```
To run the script, install `GWO`:
```console
pip install GWO
```