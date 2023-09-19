import os
import glob
import yaml
import shutil
from build_config import Config
from hooks import OpenapiHookBase, RequestHookBase, SchemasHookBase, OtherHookBase
from tqdm import tqdm


def replace_ref(x):
    if isinstance(x, dict):
        return {
            key: "#" + value.split("#")[-1] if key == "$ref" else replace_ref(value)
            for key, value in x.items()
        }
    elif isinstance(x, list):
        return [replace_ref(value) for value in x]
    return x


print("=== Build Start ===")


config = Config()


shutil.rmtree("dist", ignore_errors=True)


for lang, profile in tqdm(config.main().items(), leave=False):
    paths = {}
    schemas = {}
    files = glob.glob(os.path.join(config.INPUT_DIR, "**/*.yaml"))
    for file in tqdm(files, leave=False):
        file = file.replace(os.path.sep, "/")
        with open(file, mode="r", encoding="utf-8") as f:
            load = yaml.safe_load(f)

        # RequestHookBase hook
        for path in list(load["paths"]):
            for method in list(load["paths"][path]):
                key, value = path, load["paths"][path][method]
                for tag in list(load["paths"][path][method].get("tags", ["default"])):
                    for hook in profile["request"][tag]:
                        hook: RequestHookBase
                        key, value = hook.hook(key, value)
                paths.update({key: {}})
                paths[key].update({method: value})

        # SchemasHookBase hook
        for name in list(load.get("components", {}).get("schemas", {})):
            value = load["components"]["schemas"][name]
            for hook in profile["schemas"]:
                hook: SchemasHookBase
                value = hook.hook(value)
            schemas.update({name: value})

        # OtherHookBase hook
        if file == "src/openapi/paths/other.yaml":
            for hook in profile["other"]:
                hook: OtherHookBase
                key, value = hook.hook()
                schemas["OtherResponse"]["properties"].append({key: value})

    file = "src/openapi/openapi-3.0.yaml"

    with open(file, mode="r", encoding="utf-8") as f:
        openapi = yaml.safe_load(f)

    # OpenapiHookBase hook
    for hook in profile["openapi"]:
        hook: OpenapiHookBase
        openapi = hook.hook(openapi)

    openapi["paths"] = replace_ref(paths)
    openapi["components"]["schemas"] = replace_ref(schemas)
    output = config.OUTPUT_DIR.format(lang)
    os.makedirs(output, exist_ok=True)

    with open(output + "/openapi-3.0.yaml", mode="w+", encoding="utf-8") as f:
        f.write(yaml.dump(openapi))

print("=== Build End ===")
