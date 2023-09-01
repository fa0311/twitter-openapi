import json
import os
import logging
import base64
import openapi_client as pt
from pathlib import Path
import time
import glob

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("test_serialize")

TWITTER_SESSION = os.environ.get("TWITTER_SESSION", None)
ERROR_UNCATCHED = os.environ.get("ERROR_UNCATCHED", "false").lower() == "true"
SLEEP_TIME = float(os.environ.get("SLEEP", "0"))
CUESOR_TEST_COUNT = int(os.environ.get("CUESOR_TEST_COUNT", "3"))


if Path("cookie.json").exists():
    with open("cookie.json", "r") as f:
        cookies = json.load(f)
elif TWITTER_SESSION is not None:
    data = base64.b64decode(TWITTER_SESSION).decode("utf-8")
    cookies = json.loads(data)
else:
    commands = ["python -m pip install tweepy_authlib", "python tools/login.py"]
    raise Exception(f'cookie.json not found. Please run `{"; ".join(commands)}` first.')

cookies_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])


with open("src/config/placeholder.json", "r") as f:
    placeholder = json.load(f)


def get_key(snake_str):
    components = snake_str.split("_")
    return "".join(x.title() for x in components[1:])


def get_cursor(obj, fn):
    res = []
    if type(obj) == dict:
        callback = fn(obj)
        if callback is not None:
            res.extend(callback)
        else:
            for v in obj.values():
                res.extend(get_cursor(v, fn))
    elif type(obj) == list:
        for v in obj:
            res.extend(get_cursor(v, fn))
    return res


def find_cursor(x):
    if x.get("__typename") is pt.TypeName.TIMELINETIMELINECURSOR:
        return [x["value"]]


def find_name(x):
    if x.get("name") is not None:
        return [x["name"]]


def get_kwargs(key, additional):
    kwargs = {"path_query_id": placeholder[key]["queryId"]}
    if placeholder[key].get("variables") is not None:
        kwargs["variables"] = json.dumps(placeholder[key]["variables"] | additional)
    if placeholder[key].get("features") is not None:
        kwargs["features"] = json.dumps(placeholder[key]["features"])
    if placeholder[key].get("fieldToggles") is not None:
        kwargs["field_toggles"] = json.dumps(placeholder[key]["fieldToggles"])
    return kwargs


def save_cache(data):
    rand = time.time_ns()
    os.makedirs("cache", exist_ok=True)
    with open(f"cache/{rand}.json", "w+") as f:
        json.dump(data, f, indent=4)


for file in glob.glob("cache/*.json"):
    with open(file, "r") as f:
        cache = json.load(f)
    data = pt.__dict__[cache["type"]].from_json(cache["raw"])

logger.info(f"Success: {len(glob.glob('cache/*.json'))}")


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
        if props.startswith("__") or not props.endswith("_with_http_info"):
            continue

        key = get_key(props[:-17])
        cursor_list = set([None])
        cursor_history = set()

        try:
            for _ in range(CUESOR_TEST_COUNT):
                cursor = cursor_list.pop()
                cursor_history.add(cursor)
                logger.info(f"Try: {key} {cursor}")

                kwargs = get_kwargs(key, {} if cursor is None else {"cursor": cursor})
                res: pt.ApiResponse = getattr(x(api_client), props)(**kwargs)
                data = res.data.to_dict()

                save_cache({"raw": res.raw_data, "type": res.data.__class__.__name__})

                new_cursor = set(get_cursor(data, find_cursor)) - cursor_history
                cursor_list.update(new_cursor)
                # logger.info(f"Find cursor: {len(new_cursor)}")

                if data.get("errors") is not None:
                    logger.error(data)
                    error_count += 1

                if len(cursor_list) == 0:
                    break
                time.sleep(SLEEP_TIME)

        except Exception as e:
            if ERROR_UNCATCHED:
                raise
            import traceback

            logger.error("==========[STACK TRACE]==========")
            for trace in traceback.format_exc().split("\n"):
                logger.error(trace)
            logger.info("================================")
            error_count += 1

if error_count > 0:
    exit(1)
