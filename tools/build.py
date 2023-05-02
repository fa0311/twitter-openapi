import os
import glob
import json
import yaml
import shutil
import copy
import re
from build_config import Config


print("=== Build Start ===")


config = Config()


try:
    shutil.rmtree("dist")
except:
    pass

for lang in config.main().keys():
    dist_replace = lambda x: x.replace(
        config.INPUT_DIR, config.OUTPUT_DIR.format(lang), 1
    )

    for dir in glob.glob(os.path.join(config.INPUT_DIR, "**/")):
        os.makedirs(dist_replace(dir), exist_ok=True)

    paths = {}
    for file in glob.glob(os.path.join(config.INPUT_DIR, "**/*.yaml")):
        file = file.replace(os.path.sep, "/")
        with open(file, mode="r", encoding="utf-8") as f:
            load = yaml.safe_load(f)
        for path in list(load["paths"]):
            for method in list(load["paths"][path]):
                for tag in list(load["paths"][path][method].get("tags", ["default"])):
                    key, value = path, load["paths"][path][method]
                    for hook in config.main()[lang]["request"][tag]:
                        key, value = hook.hook(key, value)
                    load["paths"][path][method] = value
                    load["paths"][key] = load["paths"].pop(path)

            escape = path.replace("/", "~1")
            relative = file.replace(config.INPUT_DIR, "", 1)
            paths.update({key: {"$ref": f".{relative}#/paths/{escape}"}})

        with open(dist_replace(file), mode="w+", encoding="utf-8") as f:
            f.write(yaml.dump(load))

    file = "src/openapi/openapi-3.0.yaml"
    with open(file, mode="r", encoding="utf-8") as f:
        openapi = yaml.safe_load(f)
    for path in paths:
        load["paths"] = paths
    with open(dist_replace(file), mode="w+", encoding="utf-8") as f:
        f.write(yaml.dump(load))

print("=== Build End ===")
