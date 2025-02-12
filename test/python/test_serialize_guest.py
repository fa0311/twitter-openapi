import json
import re
from urllib.parse import urlencode, urlparse

import openapi_client as pt
import urllib3


def get_kwargs(key, additional):
    kwargs = {"path_query_id": placeholder[key]["queryId"]}
    if placeholder[key].get("variables") is not None:
        kwargs["variables"] = json.dumps(placeholder[key]["variables"] | additional)
    if placeholder[key].get("features") is not None:
        kwargs["features"] = json.dumps(placeholder[key]["features"])
    if placeholder[key].get("fieldToggles") is not None:
        kwargs["field_toggles"] = json.dumps(placeholder[key]["fieldToggles"])
    return kwargs




class SessionManager:
    def __init__(self) -> None:
        header = "https://raw.githubusercontent.com/fa0311/latest-user-agent/refs/heads/main/header.json"
        self.http = urllib3.PoolManager()
        self.chorome_header = json.loads(self.http.request("GET", header).data)

    
    def child(self):
        return SessionManagerChild(self.http,self.chorome_header)

class SessionManagerChild:
    def __init__(self, http, chorome_header) -> None:
        self.http = http
        self.chorome_header = chorome_header
        self.session = {}
        
    def cookie_normalize(self, cookie: list[str]) -> dict[str, str]:
        value = {x.split("; ")[0].split("=")[0]: x.split("; ")[0].split("=")[1] for x in cookie}
        return {key: value[key] for key in value if len(value[key]) > 0}

    def cookie_to_str(self, cookie: dict[str, str]) -> str:
        return "; ".join([f"{key}={value}" for key, value in cookie.items()])
    
    def getHader(self, additionals={}) -> dict[str, str]:
        ignore = ["host", "connection"]
        base = {key: value for key, value in self.chorome_header["chrome"].items() if key not in ignore}
        return base | {"cookie": self.cookie_to_str(self.session)} | additionals
    
    def update_normalize(self, cookie: list[str]):
        self.update(self.cookie_normalize(cookie))
    
    def update(self, cookie: dict[str, str]):
        self.session.update(cookie)
    
    def pop(self, key: str):
        self.session.pop(key)
    
    def get(self, key: str):
        return self.session.get(key)
    
    def to_str(self):
        return self.cookie_to_str(self.session)
        

def get_guest_token():
    twitter_url = "https://x.com/elonmusk"
    http = urllib3.PoolManager()
    chrome = SessionManager()
    x = chrome.child()
    twitter = chrome.child()
    

    
    def regex(str: str, **kwargs) -> str:
        return str.format(
            quote=r"[\'\"]",
            space=r"\s*",
            dot=r"\.",
            any=r".*?",
            target=r"([\s\S]*?)",
            **kwargs
        )
    

    def redirect(method: str, url: str, body: str = None, headers: dict[str, str] = {}) -> urllib3.HTTPResponse:
        for _ in range(10):
            if urlparse(url).netloc == "x.com":
                res = http.request(method, url, headers=x.getHader(headers), body=body, redirect=False)
                x.update_normalize(res.headers._container["set-cookie"][1:])
            elif urlparse(url).netloc == "twitter.com":
                res = http.request(method, url, headers=twitter.getHader(headers), body=body, redirect=False)
                twitter.update_normalize(res.headers._container["set-cookie"][1:])
            else:
                raise Exception("Invalid domain")
        
            method = "GET"
            body = None
            headers = {}
            location = "document{dot}location{space}={space}{quote}{target}{quote}"
            submit = "document{dot}forms{dot}{target}{dot}submit"
            form = "<form{space}action{space}={space}{quote}{target}{quote}{space}method{space}={space}{quote}post{quote}{space}name{space}={space}{quote}{name}{quote}>{target}</form>"
            input = "<input{space}type{space}={space}{quote}hidden{quote}{space}name{space}={space}{quote}{target}{quote}{space}value{space}={space}{quote}{target}{quote}{space}/>"

            if res.status >= 300 and res.status < 400:
                new_path = res.headers._container["location"][1]
                if new_path.startswith("/"):
                    domain = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                    url = f"{domain}{new_path}"
                else:
                    url = new_path
            
            elif re.findall(regex(location), res.data.decode()):
                url = re.findall(regex(location), res.data.decode())[0]
            elif re.findall(regex(submit), res.data.decode()):
                name = re.findall(regex(submit), res.data.decode())
                form_html = re.findall(regex(form, name=name[0]), res.data.decode())
                input_html = re.findall(regex(input), form_html[0][1])
                method = "POST"
                url = form_html[0][0]
                body = urlencode({k:v for k,v in input_html})
                headers = {"content-type": "application/x-www-form-urlencoded"}
            elif res.status == 200:
                return res
            else:
                raise Exception("Failed to redirect")
        else:
            raise Exception("Failed to redirect")
    
    res = redirect("GET", twitter_url)
    reg = "document{dot}cookie{space}={space}{quote}{target}{quote}"
    if  re.findall(regex(reg), res.data.decode()):
        find = re.findall(regex(reg), res.data.decode())
        x.update_normalize(find)

    if x.get("gt") is None:
        raise Exception("Failed to get guest token")

    
    return x



if __name__ == "__main__":
    cookies = get_guest_token()
    cookies_str = cookies.to_str()

    with open("src/config/placeholder.json", "r") as f:
        placeholder = json.load(f)

    api_conf = pt.Configuration(
        api_key={
            "ClientLanguage": "en",
            "ActiveUser": "yes",
            "GuestToken": cookies.get("gt"),
        },
    )

    latest_user_agent_res = urllib3.PoolManager().request(
        "GET",
        "https://raw.githubusercontent.com/fa0311/latest-user-agent/main/output.json",
    )

    latest_user_agent = json.loads(latest_user_agent_res.data.decode("utf-8"))

    api_conf.access_token = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
    api_client = pt.ApiClient(configuration=api_conf, cookie=cookies_str)
    api_client.user_agent = latest_user_agent["chrome-fetch"]

    res = pt.TweetApi(api_client).get_user_tweets_with_http_info(
        **get_kwargs("UserTweets", {}),
    ).model_dump_json()
    res = pt.TweetApi(api_client).get_user_highlights_tweets_with_http_info(
        **get_kwargs("UserHighlightsTweets", {}),
    ).model_dump_json()
    res = pt.DefaultApi(api_client).get_tweet_result_by_rest_id_with_http_info(
        **get_kwargs("TweetResultByRestId", {}),
    ).model_dump_json()
    res = pt.UserApi(api_client).get_user_by_screen_name_with_http_info(
        **get_kwargs("UserByScreenName", {})
    ).model_dump_json()
