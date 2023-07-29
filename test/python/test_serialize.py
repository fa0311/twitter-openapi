import json
import os
import logging
import base64
import python_generated as pt
from pathlib import Path


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("test_serialize")

if Path("cookie.json").exists():
    with open("cookie.json", "r") as f:
        cookies = json.load(f)
else:
    data = base64.b64decode(os.environ["TWITTER_SESSION"]).decode("utf-8")
    cookies = json.loads(data)

cookies_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])


with open("src/config/placeholder.json", "r") as f:
    placeholder = json.load(f)


def getKey(snake_str):
    components = snake_str.split("_")
    return "".join(x.title() for x in components[1:])


api_conf = pt.Configuration(
    api_key={
        "ClientLanguage": "en",
        "ActiveUser": "yes",
        "AuthType": "OAuth2Session",
        "CsrfToken": cookies["ct0"],
    },
)

api_conf.access_token = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

api_client = pt.ApiClient(configuration=api_conf, cookie=cookies_str)
api_client.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"

error_count = 0

for x in [pt.DefaultApi, pt.TweetApi, pt.UserApi, pt.UserListApi]:
    for props, fn in x.__dict__.items():
        if not callable(fn):
            continue
        if props.startswith("__") or props.endswith("_with_http_info"):
            continue

        key = getKey(props)
        logger.info(f"Try: {key}")

        kwargs = {"path_query_id": placeholder[key]["queryId"]}
        if placeholder[key].get("variables") is not None:
            kwargs["variables"] = json.dumps(placeholder[key]["variables"])
        if placeholder[key].get("features") is not None:
            kwargs["features"] = json.dumps(placeholder[key]["features"])
        if placeholder[key].get("fieldToggles") is not None:
            kwargs["field_toggles"] = json.dumps(placeholder[key]["fieldToggles"])

        try:
            res = getattr(x(api_client), props)(**kwargs)
        except Exception as e:
            logger.error(f"{key}")
            logger.error(e)
            error_count += 1

if error_count > 0:
    exit(1)
