"""Sync src/config/placeholder.json with the current X frontend.

    uv run tools/update_placeholder.py                        # queryId/features from TwitterInternalAPIDocument
    uv run tools/update_placeholder.py --browser              # also record the real requests x.com makes (needs cookie.json)
    uv run tools/update_placeholder.py --relay requests.ndjson  # also apply requests exported from twitter_api_safe_relay

The static step covers every GraphQL entry. The browser step replaces the DevTools
"copy all as fetch" workflow: it opens x.com with the cookies in cookie.json, visits a
set of pages and records queryId / method / features / fieldToggles exactly as the
frontend sends them, then warns when the recorded variables differ from the placeholder.
The relay step reads the NDJSON that the twitter_api_safe_relay dashboard exports
(one hooked API client request per line), which also covers mutations triggered by hand.
"""

import argparse
import json
import os
import random
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

PLACEHOLDER = Path("src/config/placeholder.json")
COOKIE = Path("cookie.json")
GRAPHQL_JSON = "https://raw.githubusercontent.com/fa0311/TwitterInternalAPIDocument/develop/docs/json/GraphQL.json"
HEADER_JSON = "https://raw.githubusercontent.com/fa0311/latest-user-agent/refs/heads/main/header.json"
GRAPHQL_PATH = re.compile(r"/i/api/graphql/(?P<query_id>[^/]+)/(?P<name>[^/?]+)")

TWEET = "1349129669258448897"
USER = "elonmusk"
PAGES = [
    "/home",
    "/explore",
    "/notifications",
    "/i/bookmarks",
    f"/{USER}",
    f"/{USER}/with_replies",
    f"/{USER}/highlights",
    f"/{USER}/media",
    f"/{USER}/followers",
    f"/{USER}/following",
    f"/{USER}/verified_followers",
    f"/{USER}/followers_you_follow",
    f"/{USER}/status/{TWEET}",
    f"/{USER}/status/{TWEET}/likes",
    f"/{USER}/status/{TWEET}/retweets",
    "/search?q=twitter&src=typed_query",
    "/search?q=twitter&src=typed_query&f=live",
    "/i/lists/1141162794290520064",
    "/i/lists/1141162794290520064/members",
    "/i/lists/1141162794290520064/followers",
    "/i/communities/1493446837214187523",
    "/i/communities/1493446837214187523/media",
    "/i/communities/1493446837214187523/about",
    "/i/communities_explore",
    "/i/grok",
    "/i/lists",
    "/compose/post",
]
# pages under the logged-in user's own screen name are added at runtime (likes etc.)
SELF_PAGES = ["/{me}/likes", "/{me}/lists"]


def load_json(source: str):
    if source.startswith("http"):
        return requests.get(source, timeout=60).json()
    return json.load(Path(source).open(encoding="utf-8"))


def is_graphql(entry) -> bool:
    return isinstance(entry, dict) and "@path" in entry


def sync_static(placeholder: dict, graphql_json: str) -> list[str]:
    docs = {e["exports"]["operationName"]: e["exports"] for e in load_json(graphql_json)}
    changed = []
    for name, entry in placeholder.items():
        if not is_graphql(entry) or name not in docs:
            continue
        doc = docs[name]
        values = doc["metadata"].get("featureSwitch", {})
        features = {
            key: values[key]["value"] == "true" if key in values else entry.get("features", {}).get(key, False)
            for key in doc["metadata"]["featureSwitches"]
        }
        before = json.dumps([entry["queryId"], entry.get("features")], sort_keys=True)
        entry["queryId"] = doc["queryId"]
        entry["@path"] = f"/i/api/graphql/{doc['queryId']}/{name}"
        if doc["metadata"]["featureSwitches"]:
            entry["features"] = features
        if before != json.dumps([entry["queryId"], entry.get("features")], sort_keys=True):
            changed.append(name)
    missing = [name for name, entry in placeholder.items() if is_graphql(entry) and name not in docs]
    if missing:
        print(f"not in TwitterInternalAPIDocument: {', '.join(missing)}")
    return changed


def parse_request(method: str, url: str, body: str | None) -> dict:
    if method == "GET":
        query = parse_qs(urlparse(url).query)
        return {key: json.loads(values[0]) for key, values in query.items() if key in ["variables", "features", "fieldToggles"]}
    data = json.loads(body or "{}")
    return {key: data[key] for key in ["variables", "features", "fieldToggles"] if key in data}


def get_proxy():
    """PROXY_LIST: one HTTP CONNECT proxy URL per line (http://user:pass@host:port), as in the other repositories."""
    proxies = [x.strip() for x in os.environ.get("PROXY_LIST", "").splitlines() if x.strip()]
    if not proxies:
        return None
    proxy = random.choice(proxies)
    if "://" not in proxy:  # legacy host:port:user:pass
        host, port, username, password = proxy.split(":")
        proxy = f"http://{username}:{password}@{host}:{port}"
    parsed = urlparse(proxy)
    return {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}", "username": parsed.username, "password": parsed.password}


def record_requests(pages: list[str]) -> dict[str, dict]:
    from playwright.sync_api import sync_playwright

    cookies = json.load(COOKIE.open(encoding="utf-8"))
    if isinstance(cookies, dict):
        cookies = [{"name": key, "value": value, "domain": ".x.com"} for key, value in cookies.items()]
    same_site = {"no_restriction": "None", "lax": "Lax", "strict": "Strict"}
    cookies = [
        {
            "name": c["name"],
            "value": c["value"],
            "domain": c.get("domain", ".x.com"),
            "path": c.get("path", "/"),
            "secure": c.get("secure", True),
            "httpOnly": c.get("httpOnly", False),
            "sameSite": same_site.get(c.get("sameSite"), "None"),
        }
        for c in cookies
        if c.get("domain", ".x.com").endswith("x.com")
    ]
    user_agent = load_json(HEADER_JSON)["chrome"]["user-agent"]

    recorded: dict[str, dict] = {}

    def on_request(request):
        match = GRAPHQL_PATH.search(request.url)
        if match is None or match["name"] in recorded:
            return
        recorded[match["name"]] = {
            "@path": f"/i/api/graphql/{match['query_id']}/{match['name']}",
            "@method": request.method,
            "queryId": match["query_id"],
            **parse_request(request.method, request.url, request.post_data),
        }

    with sync_playwright() as p:
        browser = p.chromium.launch(proxy=get_proxy())
        context = browser.new_context(user_agent=user_agent, viewport={"width": 1280, "height": 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.set_default_navigation_timeout(120000)  # the proxies are slow
        page.on("request", on_request)
        page.goto("https://x.com/home")
        me = page.get_attribute('a[data-testid="AppTabBar_Profile_Link"]', "href", timeout=120000)
        for path in pages + [path.format(me=me) for path in SELF_PAGES if me]:
            print(f"visit {path}")
            page.goto(f"https://x.com{path}")
            page.wait_for_timeout(6000)
        browser.close()
    return recorded


def check_variables(name: str, placeholder: dict, recorded: dict):
    for key in placeholder.keys() | recorded.keys():
        if key not in placeholder:
            print(f"{name}: variables.{key} is new ({recorded[key]!r})")
        elif key not in recorded:
            print(f"{name}: variables.{key} is not sent anymore")


def apply_recorded(placeholder: dict, recorded: dict[str, dict]) -> list[str]:
    changed = []
    for name, entry in placeholder.items():
        if not is_graphql(entry) or name not in recorded:
            continue
        hit = recorded[name]
        before = json.dumps(entry, sort_keys=True)
        entry["@path"] = hit["@path"]
        entry["@method"] = hit["@method"]
        entry["queryId"] = hit["queryId"]
        for key in ["features", "fieldToggles"]:
            if key in hit:
                entry[key] = hit[key]
        if "variables" in hit and "variables" in entry:
            check_variables(name, entry["variables"], hit["variables"])
        if before != json.dumps(entry, sort_keys=True):
            changed.append(name)
    print(f"recorded {len(recorded)} operations, {len(set(recorded) - set(placeholder))} not in placeholder")
    return changed


def sync_browser(placeholder: dict, pages: list[str]) -> list[str]:
    return apply_recorded(placeholder, record_requests(pages))


def read_relay(path: str) -> dict[str, dict]:
    """Requests exported by the twitter_api_safe_relay dashboard: the X web client's own request objects."""
    recorded: dict[str, dict] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        request = json.loads(line)
        match = re.fullmatch(r"/graphql/(?P<query_id>[^/]+)/(?P<name>[^/?]+)", request["path"])
        if match is None or match["name"] in recorded:
            continue
        if request["method"] == "GET":
            params = request.get("params", {})
            payload = {key: json.loads(params[key]) for key in ["variables", "features", "fieldToggles"] if key in params}
        else:
            data = request.get("data", {})
            payload = {key: data[key] for key in ["variables", "features", "fieldToggles"] if key in data}
        recorded[match["name"]] = {
            "@path": f"/i/api{request['path']}",
            "@method": request["method"],
            "queryId": match["query_id"],
            **payload,
        }
    return recorded


def sync_relay(placeholder: dict, path: str) -> list[str]:
    return apply_recorded(placeholder, read_relay(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--browser", action="store_true", help="also record requests from x.com using cookie.json")
    parser.add_argument("--page", action="append", help="extra page path to visit (repeatable)")
    parser.add_argument("--relay", metavar="NDJSON", help="requests exported from the twitter_api_safe_relay dashboard")
    parser.add_argument("--graphql-json", default=GRAPHQL_JSON, help="TwitterInternalAPIDocument GraphQL.json (URL or path)")
    args = parser.parse_args()

    placeholder = json.load(PLACEHOLDER.open(encoding="utf-8"))
    changed = sync_static(placeholder, args.graphql_json)
    print(f"static: updated {len(changed)} entries")
    if args.browser:
        changed = sync_browser(placeholder, PAGES + (args.page or []))
        print(f"browser: updated {len(changed)} entries: {', '.join(changed)}")
    if args.relay:
        changed = sync_relay(placeholder, args.relay)
        print(f"relay: updated {len(changed)} entries: {', '.join(changed)}")
    with PLACEHOLDER.open("w", encoding="utf-8") as f:
        json.dump(placeholder, f, indent=4)


if __name__ == "__main__":
    main()
