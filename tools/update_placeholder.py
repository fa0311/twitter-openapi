"""Sync src/config/placeholder.json with the requests the X frontend really sends.

    uv run tools/update_placeholder.py --browser                 # record x.com with the cookies in cookie.json
    uv run tools/update_placeholder.py --relay requests.ndjson   # apply requests exported from twitter_api_safe_relay
    uv run tools/update_placeholder.py --browser --relay requests.ndjson

The browser step replaces the DevTools "copy all as fetch" workflow: it opens x.com with the
cookies in cookie.json, visits a set of pages and records queryId / method / features /
fieldToggles exactly as the frontend sends them, then warns when the recorded variables differ
from the placeholder. The relay step reads the NDJSON that the twitter_api_safe_relay dashboard
exports (one hooked API client request per line), which also covers mutations triggered by hand.
Only recorded operations are touched: the entries that were not recorded are listed at the end
and have to be checked by hand.
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
    "/i/connect_people",
    "/i/communitynotes",
    "/i/trends",
    "/i/communities/suggested",
    f"/{USER}/superfollows",
    f"/{USER}/lists",  # CombinedLists
    "/i/lists/search?q=test",  # ListSearchTimeline
    "/i/communities/suggested?q=test",  # CommunitiesSearchQuery, GlobalCommunities*PostSearchTimeline
]
# pages under the logged-in user's own screen name are added at runtime (likes etc.)
SELF_PAGES = ["{me}/likes", "{me}/lists"]  # {me} is the profile link, "/<screen_name>"
# page-local search boxes that only open on click: path -> aria-label of the button / placeholder of the input
SEARCH_BOXES = {"/i/bookmarks": "Search Bookmarks"}  # BookmarkSearchTimeline


def is_graphql(entry) -> bool:
    return isinstance(entry, dict) and "@path" in entry


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
    parsed = urlparse(random.choice(proxies))
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
    user_agent = requests.get(HEADER_JSON, timeout=60).json()["chrome"]["user-agent"]

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
            if path in SEARCH_BOXES:  # before the tabs: the box belongs to the first tab
                page.locator(f'[aria-label="{SEARCH_BOXES[path]}"]').first.click()
                page.get_by_placeholder(SEARCH_BOXES[path]).first.fill("test")
                page.keyboard.press("Enter")
                page.wait_for_timeout(6000)
            for tab in page.locator('[role="tab"]').all():  # Following, Media, Latest, ... are not reachable by URL
                try:
                    tab.click(timeout=3000)
                    page.wait_for_timeout(3000)
                except Exception:
                    pass
        browser.close()
    return recorded


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


def check_variables(name: str, placeholder: dict, recorded: dict):
    """Report key drift only; values are the maintainer's business (a trailing ? marks an optional key)."""
    known = {key.rstrip("?") for key in placeholder}
    for key in recorded.keys() - known:
        print(f"{name}: variables.{key} is new ({recorded[key]!r})")
    for key in placeholder.keys() - recorded.keys():
        if not key.endswith("?"):
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
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--browser", action="store_true", help="record requests from x.com using cookie.json")
    parser.add_argument("--page", action="append", help="extra page path to visit (repeatable)")
    parser.add_argument("--relay", metavar="NDJSON", help="requests exported from the twitter_api_safe_relay dashboard")
    args = parser.parse_args()
    if not args.browser and not args.relay:
        parser.error("nothing to do: pass --browser and/or --relay")

    placeholder = json.load(PLACEHOLDER.open(encoding="utf-8"))
    recorded: dict[str, dict] = {}
    if args.browser:
        recorded.update(record_requests(PAGES + (args.page or [])))
    if args.relay:
        recorded.update(read_relay(args.relay))  # requests made by hand win over the page visits
    changed = apply_recorded(placeholder, recorded)
    names = [name for name, entry in placeholder.items() if is_graphql(entry)]
    print(f"recorded {len(recorded)} operations, updated {len(changed)}: {', '.join(changed)}")
    print(f"recorded but not in placeholder: {', '.join(sorted(set(recorded) - set(names)))}")
    print(f"not recorded, left as is: {', '.join(name for name in names if name not in recorded)}")
    with PLACEHOLDER.open("w", encoding="utf-8") as f:
        json.dump(placeholder, f, indent=4)


if __name__ == "__main__":
    main()
