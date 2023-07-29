import json
import base64
from tweepy_authlib import CookieSessionUserHandler


auth_handler = CookieSessionUserHandler(
    screen_name=input("screen_name: "),
    password=input("password: "),
)


cookies = auth_handler.get_cookies()

data = json.dumps(cookies.get_dict())
print(base64.b64encode(data.encode("utf-8")).decode("utf-8"))
