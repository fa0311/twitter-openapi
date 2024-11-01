import json
from pathlib import Path

import requests

if Path("cookie.json").exists():
    with open("cookie.json", "r") as f:
        cookies = json.load(f)
    cookies_dict = {k["name"]: k["value"] for k in cookies}


data = requests.get(
    "https://twitter.com/i/api/graphql/BQ6xjFU6Mgm-WhEP3OiT9w/UserByScreenName",
    cookies=cookies_dict,
    headers={
        "accept": "*/*",
        "accept-encoding": "identity",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        "content-type": "application/json",
        "referer": "https://twitter.com",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/Chrome/130.0.0.0 Safari/537.36",
        "x-csrf-token": cookies_dict["ct0"],
        "x-twitter-active-user": "yes",
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-client-language": "en",
    },
    params={
        "variables": json.dumps(
            {
                "screen_name": "5unsetpowerln",
            },
        ),
        "features": json.dumps(
            {
                "hidden_profile_subscriptions_enabled": True,
                "rweb_tipjar_consumption_enabled": True,
                "responsive_web_graphql_exclude_directive_enabled": True,
                "verified_phone_label_enabled": False,
                "subscriptions_verification_info_is_identity_verified_enabled": True,
                "subscriptions_verification_info_verified_since_enabled": True,
                "highlights_tweets_tab_ui_enabled": True,
                "responsive_web_twitter_article_notes_tab_enabled": True,
                "subscriptions_feature_can_gift_premium": True,
                "creator_subscriptions_tweet_preview_api_enabled": True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                "responsive_web_graphql_timeline_navigation_enabled": True,
            }
        ),
        "fieldToggles": json.dumps(
            {
                "withAuxiliaryUserLabels": False,
            },
        ),
    },
)
print(data.json())
