import json
from pathlib import Path

import openapi_client as pt


def get_kwargs(key, additional):
    kwargs = {"path_query_id": placeholder[key]["queryId"]}
    if placeholder[key].get("variables") is not None:
        kwargs["variables"] = json.dumps(placeholder[key]["variables"] | additional)
    if placeholder[key].get("features") is not None:
        kwargs["features"] = json.dumps(placeholder[key]["features"])
    if placeholder[key].get("fieldToggles") is not None:
        kwargs["field_toggles"] = json.dumps(placeholder[key]["fieldToggles"])
    return kwargs


if __name__ == "__main__":
    if Path("cookie.json").exists():
        with open("cookie.json", "r") as f:
            cookies = json.load(f)
    cookies_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])

    with open("src/config/placeholder.json", "r") as f:
        placeholder = json.load(f)

    api_conf = pt.Configuration(
        api_key={
            "ClientLanguage": "en",
            "ActiveUser": "yes",
            "GuestToken": cookies["gt"],
        },
    )
    api_conf.access_token = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
    api_client = pt.ApiClient(configuration=api_conf, cookie=cookies_str)
    api_client.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"

    pt.TweetApi(api_client).get_user_tweets_with_http_info(
        **get_kwargs("UserTweets", {}),
    )
    pt.TweetApi(api_client).get_user_highlights_tweets_with_http_info(
        **get_kwargs("UserHighlightsTweets", {}),
    )
    pt.DefaultApi(api_client).get_tweet_result_by_rest_id_with_http_info(
        **get_kwargs("TweetResultByRestId", {}),
    )
    pt.UserApi(api_client).get_user_by_screen_name_with_http_info(
        **get_kwargs("UserByScreenName", {})
    )
