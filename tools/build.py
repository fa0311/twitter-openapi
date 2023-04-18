import os
import glob
import json
import yaml
import shutil


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


OUTPUT_DIR = "dist"
INPUT_DIR = "src/openapi"


def read(file: str):
    with open(file, mode="r", encoding="utf-8") as f:
        return f.read()


def write(file: str, data: str) -> None:
    with open(file.replace(INPUT_DIR, OUTPUT_DIR, 1), mode="w+", encoding="utf-8") as f:
        f.write(data)


def get_yaml(data, key):
    return yaml.safe_load(placeholder.replace_file(str(data), key))


shutil.rmtree("dist")
for dir in glob.glob(os.path.join(INPUT_DIR, "**/")):
    os.makedirs(dir.replace(INPUT_DIR, OUTPUT_DIR, 1), exist_ok=True)

placeholder = placeholder_manager()
parameters = read("src/config/parameters.yaml")
header = read("src/config/header.yaml")

paths = {}
for file in glob.glob(os.path.join(INPUT_DIR, "**/*.yaml")):
    file = file.replace(os.path.sep, "/")
    relative = file.replace(INPUT_DIR, "", 1)

    load = yaml.safe_load(placeholder.replace(read(file)))

    for key in load["paths"].keys():
        append = get_yaml(parameters, key.split("/")[-1])
        req = load["paths"][key]["get"]
        req["parameters"] = append["paths"]["/parameters"]["get"]["parameters"]

        append = get_yaml(header, key.split("/")[-1])
        req = load["paths"][key]["get"]
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
