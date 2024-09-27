# https://github.com/tsukumijima/KonomiTV/blob/master/server/misc/TwitterAPIQueryGenerator.py
# https://github.com/tsukumijima/KonomiTV/blob/master/License.txt

#!/usr/bin/env python3

# Usage: poetry run python -m misc.TwitterAPIQueryGenerator

import json
import re
import urllib.parse

from rich import print
from rich.rule import Rule


def main():
    print(Rule(characters="="))
    print(
        "Chrome DevTools の Network タブで「表示されているものをすべてfetch としてコピー」したコードを`input.js`に貼り付けてください。"
    )
    print("Enter を押すと続行します。")
    print(Rule(characters="="))
    input()

    with open("./tools/input.js", "r") as f:
        fetch_code_raw = f.read()

    print(Rule(characters="="))

    splited = fetch_code_raw.split("\n")
    fetch_code_list = []
    code = ""
    for line in splited:
        if line.startswith("fetch("):
            if code:
                fetch_code_list.append(code)
            code = line
        else:
            code += line + "\n"
    fetch_code_list.append(code)

    for fetch_code in fetch_code_list:
        # query_idとendpointを抽出
        query_id_match = re.search(r'/i/api/graphql/([^/]+)/([^"?]+)', fetch_code)
        if not query_id_match:
            print("query_id と endpoint の抽出に失敗しました。")
            print(Rule(characters="="))
            return
        query_id = query_id_match.group(1)
        endpoint = query_id_match.group(2)

        # リクエストメソッドを判定
        method_match = re.search(r'"method"\s*:\s*"(GET|POST)"', fetch_code)
        if not method_match:
            print("リクエストメソッドの判定に失敗しました。")
            print(Rule(characters="="))
            return
        method = method_match.group(1)

        if method == "POST":
            # POST リクエストの場合、fetch() コードの第二引数にある {} で囲まれたオブジェクトを正規表現で抽出したものを JSON としてパース
            body_match = re.search(r'"body"\s*:\s*"({.*})"', fetch_code, re.DOTALL)
            if not body_match:
                print("body の抽出に失敗しました。")
                print(Rule(characters="="))
                return
            body_json_str = body_match.group(1).replace("\\", "")
            body_json = json.loads(body_json_str)
            features = body_json.get("features", None)
        else:
            # GET リクエストの場合、まず URL を抽出
            url_match = re.search(r'"(https?://[^"]+)"', fetch_code)
            if not url_match:
                print("URL の抽出に失敗しました。")
                print(Rule(characters="="))
                return
            url = url_match.group(1)

            # URL をパースして query string を取得
            parsed_url = urllib.parse.urlparse(url)
            query_string = parsed_url.query

            # query string を dict 形式にパース
            query_dict = urllib.parse.parse_qs(query_string)

            # features を取得
            features_json_str = query_dict.get("features", [None])[0]
            if features_json_str is None:
                features = None
            else:
                try:
                    features = json.loads(features_json_str)
                except json.JSONDecodeError:
                    print(
                        "features の JSON パースに失敗しました。features は None として続行します。"
                    )
                    features = None

        # features を JSON としてフォーマットした後、Python の dict として正しい形式に変換
        # " を ' に置換し、true/false を True/False に置換

        # 生成するコードをフォーマット

        # ファイルに書き込む
        with open("./src/config/placeholder.json", "r") as f:
            placeholder = json.load(f)

        with open("./src/config/placeholder.json", "w") as f:
            placeholder[endpoint] = {
                **placeholder.get(endpoint, {}),
                "queryId": query_id,
                "features": features,
            }
            json.dump(placeholder, f, indent=4)


if __name__ == "__main__":
    main()
