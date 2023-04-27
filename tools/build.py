import os
import glob
import json
import yaml
import shutil
import copy
import re


class placeholder_manager:
    data: dict
    config: str = "src/config/placeholder.json"

    def __init__(self):
        with open(self.config, mode="r", encoding="utf-8") as f:
            self.data = json.load(f)

    def __replace(self, file, old: str, new) -> str:
        if type(new) is dict:
            dump = f"'{json.dumps(new)}'"
            return file.replace(f'"{old}"', dump)
        else:
            return file.replace(f"{old}", new)

    def replace(self, file: str) -> str:
        for prefix in self.data.keys():
            for key in self.data[prefix]:
                value = self.data[prefix][key]
                file = self.__replace(file, f"{{{{{prefix}{key}}}}}", value)
        return file

    def replace_file(self, file: str, prefix: str) -> str:
        if self.data.get(prefix, None) is None:
            return file
        for key in self.data[prefix].keys():
            value = self.data[prefix][key]
            file = self.__replace(file, f"{{{{{key}}}}}", value)
        return file


def placeholder_to_yaml(obj):
    if type(obj) is dict:
        return {
            "type": "object",
            "required": [i for i in obj],
            "properties": {i: placeholder_to_yaml(obj[i]) for i in obj},
            # "default": {i: placeholder_to_yaml(obj[i]) for i in obj},
            # "example": {i: placeholder_to_yaml(obj[i]) for i in obj},
        }
    elif type(obj) is list:
        if len(obj) == 0:
            return {
                "type": "array",
                "items": {"type": "object"},
                # "default": [],
                # "example": [],
            }
        return {
            "type": "array",
            "items": placeholder_to_yaml(obj[0]),
            # "default": placeholder_to_yaml(obj[0]),
            # "example": placeholder_to_yaml(obj[0]),
        }
    elif type(obj) is str:
        return {"type": "string", "example": obj, "default": obj}
    elif type(obj) is bool:
        return {"type": "boolean", "example": obj, "default": obj}
    elif type(obj) is int:
        return {"type": "integer", "example": obj, "default": obj}


print("=== Build Start ===")
OUTPUT_DIR = "dist/{0}"
INPUT_DIR = "src/openapi"
METHODS = ["get", "put", "post", "delete", "options", "head", "patch", "trace"]

try:
    shutil.rmtree("dist")
except:
    pass

with open("src/config/variable.json", mode="r", encoding="utf-8") as f:
    variable = json.load(f)


placeholder = placeholder_manager()

for lang in variable.keys():

    def read(file: str):
        with open(file, mode="r", encoding="utf-8") as f:
            return remove(f.read())

    def write(file: str, data: str) -> None:
        with open(
            file.replace(INPUT_DIR, OUTPUT_DIR.format(lang), 1),
            mode="w+",
            encoding="utf-8",
        ) as f:
            f.write(data)

    def get_yaml(data, key):
        return yaml.safe_load(placeholder.replace_file(str(data), key))

    def remove(data):
        for match in re.findall(r"(\{% (.*?) %\})", data):
            equation = match[1].split(" ")
            if equation[0] == "if" and equation[2] == "==":
                if equation[3] != variable[lang][equation[1]]:
                    data = re.sub(
                        re.escape(match[0]) + "[\s\S]*?" + re.escape("{% endif %}"),
                        "",
                        data,
                    )

        return data

    for dir in glob.glob(os.path.join(INPUT_DIR, "**/")):
        os.makedirs(dir.replace(INPUT_DIR, OUTPUT_DIR.format(lang), 1), exist_ok=True)

    parameters = read("src/config/parameters.yaml")
    header = read("src/config/header.yaml")

    paths = {}
    for file in glob.glob(os.path.join(INPUT_DIR, "**/*.yaml")):
        file = file.replace(os.path.sep, "/")
        relative = file.replace(INPUT_DIR, "", 1)

        load = yaml.safe_load(placeholder.replace(read(file)))

        for key in load["paths"].keys():
            append = get_yaml(parameters, key.split("/")[-1])
            param = append["paths"]["/parameters"]
            for method in load["paths"][key].keys():
                req = load["paths"][key][method]

                req["parameters"] = req.get("parameters", [])
                req["parameters"] += param[method].get("parameters", [])

                if param[method].get("requestBody") is not None:
                    req["requestBody"] = param[method].get("requestBody")

                if variable[lang].get(method + "_parameters") == "schema_parameters":
                    for p_key in placeholder.data[key.split("/")[-1]].keys():
                        if p_key.lower() == "query":
                            continue
                        req["parameters"].append(
                            {
                                "name": p_key.lower(),
                                "in": "query",
                                "schema": placeholder_to_yaml(
                                    placeholder.data[key.split("/")[-1]][p_key]
                                ),
                            }
                        )

                if variable[lang].get(method + "_parameters") == "schema_request_body":
                    data = placeholder.data[key.split("/")[-1]]
                    schema = {i: placeholder_to_yaml(data[i]) for i in data.keys()}

                    req["requestBody"] = {
                        "description": key.split("/")[-1] + "body",
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "properties": schema,
                                },
                            }
                        },
                    }

                append = get_yaml(header, key.split("/")[-1])
                req = load["paths"][key][method]
                req["responses"]["200"]["headers"] = append["components"]["headers"]

                escape = key.replace("/", "~1")
                paths.update({key: {"$ref": f".{relative}#/paths/{escape}"}})
        write(file, yaml.dump(load))

    file = "src/openapi/openapi-3.0.yaml"
    data = read(file)
    for path in paths:
        load = yaml.safe_load(placeholder.replace(data))
        load["paths"] = paths

    write(file, yaml.dump(load))

print("=== Build End ===")
