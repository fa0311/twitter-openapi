import json
from tweepy_authlib import CookieSessionUserHandler

auth_handler = CookieSessionUserHandler(
    screen_name=input("screen_name: "),
    password=input("password: "),
)


cookies = auth_handler.get_cookies()

print(json.dumps(cookies.get_dict()))
