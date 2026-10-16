"""Apply twitter_api_safe_relay's request catalog to src/config/placeholder.json.

    uv run tools/update_placeholder.py requests.ndjson
    uv run tools/update_placeholder.py https://raw.githubusercontent.com/fa0311/twitter_api_safe_relay/main/packages/server/requests.ndjson

The catalog (packages/server/requests.ndjson in fa0311/twitter_api_safe_relay, also served by a
running relay at /requests.ndjson) holds the X web client's own request objects, one per
operation, recorded with twitter-api-safe-dump. For every operation in the catalog that carries a
recording date (recordedAt), queryId / @method / features / fieldToggles are overwritten with exactly
what the frontend sent and the date is printed; lines of unknown age are never applied. variables
are never overwritten, only key drift is printed (a trailing ? marks an optional key). Operations
missing from the catalog are left untouched and listed at the end.
"""

import argparse
import json
import re
from pathlib import Path

import requests

PLACEHOLDER = Path("src/config/placeholder.json")


def is_graphql(entry) -> bool:
    return isinstance(entry, dict) and "@path" in entry


def read_catalog(source: str) -> dict[tuple[str, str], dict]:
    """(operation, method) -> placeholder-shaped entry; the frontend uses both GET and POST for some operations."""
    text = requests.get(source, timeout=60).text if source.startswith("http") else Path(source).read_text(encoding="utf-8")
    recorded: dict[tuple[str, str], dict] = {}
    unstamped: set[str] = set()
    for line in text.splitlines():
        if not line.strip():
            continue
        request = json.loads(line)
        match = re.fullmatch(r"/graphql/(?P<query_id>[^/]+)/(?P<name>[^/?]+)", request["path"])
        if match is None or (match["name"], request["method"]) in recorded:
            continue
        if "recordedAt" not in request:  # kept from an older catalog, age unknown: never applied to placeholder.json
            unstamped.add(match["name"])
            continue
        if request["method"] == "GET":
            params = request.get("params", {})
            payload = {key: json.loads(params[key]) for key in ["variables", "features", "fieldToggles"] if key in params}
        else:
            data = request.get("data", {})
            payload = {key: data[key] for key in ["variables", "features", "fieldToggles"] if key in data}
        recorded[(match["name"], request["method"])] = {
            "@path": f"/i/api{request['path']}",
            "@method": request["method"],
            "queryId": match["query_id"],
            "recordedAt": request["recordedAt"],
            **payload,
        }
    if unstamped:
        print(f"not applied, recording date unknown: {', '.join(sorted(unstamped))}")
    return recorded


def check_variables(name: str, placeholder: dict, recorded: dict):
    """Report key drift only; values are the maintainer's business (a trailing ? marks an optional key)."""
    known = {key.rstrip("?") for key in placeholder}
    for key in recorded.keys() - known:
        print(f"{name}: variables.{key} is new ({recorded[key]!r})")
    for key in placeholder.keys() - recorded.keys():
        if not key.endswith("?"):
            print(f"{name}: variables.{key} is not sent anymore")


def apply_recorded(placeholder: dict, recorded: dict[tuple[str, str], dict]) -> list[str]:
    """Overwrite with the recorded request. The frontend switches an operation to POST only when the query string
    would get too long (HomeLatestTimeline with seenTweetIds), so POST is taken whenever it was recorded."""
    by_name: dict[str, dict] = {}
    for (name, method), hit in recorded.items():
        by_name.setdefault(name, hit)
    changed = []
    for name, entry in placeholder.items():
        if not is_graphql(entry) or name not in by_name:
            continue
        hit = recorded.get((name, "POST"), by_name[name])
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
            changed.append(f"{name} ({hit['recordedAt'][:10]})")
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("catalog", help="twitter_api_safe_relay requests.ndjson (file or URL)")
    args = parser.parse_args()

    placeholder = json.load(PLACEHOLDER.open(encoding="utf-8"))
    recorded = read_catalog(args.catalog)
    changed = apply_recorded(placeholder, recorded)
    names = [name for name, entry in placeholder.items() if is_graphql(entry)]
    seen = {name for name, _ in recorded}
    print(f"catalog has {len(seen)} operations, updated {len(changed)}: {', '.join(changed)}")
    print(f"in the catalog but not in placeholder: {', '.join(sorted(seen - set(names)))}")
    print(f"not in the catalog, left as is: {', '.join(name for name in names if name not in seen)}")
    with PLACEHOLDER.open("w", encoding="utf-8") as f:
        json.dump(placeholder, f, indent=4)


if __name__ == "__main__":
    main()
