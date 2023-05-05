import yaml
import json


class HookBase:
    PLACEHOLDER: dict

    def __init__(self):
        with open("src/config/placeholder.json", mode="r", encoding="utf-8") as f:
            self.PLACEHOLDER = json.load(f)

    def placeholder_to_yaml(self, obj, default=False, example=False) -> dict:
        fn = lambda x: self.placeholder_to_yaml(x, default=default, example=example)
        if type(obj) is dict:
            properties = {i: fn(obj[i]) for i in obj}
            value = {
                "type": "object",
                "properties": properties,
            }
            value.update({"required": [i for i in obj]} if len(obj) > 0 else {})
            value.update({"default": properties} if default else {})
            value.update({"example": properties} if example else {})
            return value
        elif type(obj) is list and len(obj) > 0:
            properties = fn(obj[0])
            value = {
                "type": "array",
                "items": properties,
            }
            value.update({"default": [properties]} if default else {})
            value.update({"example": [properties]} if example else {})
            return value
        elif type(obj) is list and len(obj) == 0:
            value = {
                "type": "array",
                "items": {"type": "object"},
            }
            value.update({"default": []} if default else {})
            value.update({"example": []} if example else {})
            return value
        elif type(obj) is str:
            return {"type": "string", "example": obj, "default": obj}
        elif type(obj) is bool:
            return {"type": "boolean", "example": obj, "default": obj}
        elif type(obj) is int:
            return {"type": "integer", "example": obj, "default": obj}

    def load_component(self, name: str) -> dict:
        with open(f"src/config/component/{name}.yaml", mode="r", encoding="utf-8") as f:
            return yaml.safe_load(f)


# HookBase extends


class OpenapiHookBase(HookBase):
    def hook(self, value: dict):
        return value


class RequestHookBase(HookBase):
    split: int
    path_name: str

    def __init__(self, split=1):
        super().__init__()
        self.split = split

    def hook(self, path: str, value: dict):
        value["parameters"] = value.get("parameters", [])
        self.path_name = "/".join(path.split("/")[self.split :])
        return path, value


# OpenapiHookBase extends


class AddSecuritySchemesOnSecuritySchemes(OpenapiHookBase):
    def hook(self, value: dict):
        value = super().hook(value)
        component = self.load_component("security_schemes")
        param = component["components"]["securitySchemes"]
        value["components"]["securitySchemes"].extend(param)
        return value


# RequestHookBase extends


class AddSecuritySchemesOnHeader(RequestHookBase):
    def hook(self, path: str, value: dict):
        path, value = super().hook(path, value)
        component = self.load_component("security_schemes")
        param = component["paths"]["/parameters"]["get"]["parameters"]
        value["parameters"].extend(param)
        return path, value


class ReplaceQueryIdPlaceholder(RequestHookBase):
    def hook(self, path: str, value: dict):
        path, value = super().hook(path, value)
        new = self.PLACEHOLDER[self.path_name]["queryId"]
        return path.replace(r"{{queryId}}", new), value


class SetResponsesHeader(RequestHookBase):
    suffix: str

    def __init__(self, suffix: str | None = None):
        super().__init__()
        self.suffix = "" if suffix is None else "_" + suffix

    def hook(self, path: str, value: dict):
        path, value = super().hook(path, value)
        component = self.load_component("response_header" + self.suffix)
        value["responses"]["200"]["headers"] = component["components"]["headers"]
        return path, value


class AddParametersOnParametersAsString(RequestHookBase):
    def hook(self, path: str, value: dict):
        path, value = super().hook(path, value)
        for key in self.PLACEHOLDER[self.path_name].keys():
            example = json.dumps(self.PLACEHOLDER[self.path_name][key])
            value["parameters"].append(
                {
                    "name": key,
                    "in": "query",
                    "required": True,
                    "schema": {
                        "type": "string",
                        "default": example,
                        "example": example,
                    },
                }
            )
        return path, value


class AddParametersOnParametersAsObject(RequestHookBase):
    def hook(self, path: str, value: dict):
        path, value = super().hook(path, value)
        for key in self.PLACEHOLDER[self.path_name].keys():
            example = json.dumps(self.PLACEHOLDER[self.path_name][key])
            value["parameters"].append(
                {
                    "name": key,
                    "in": "query",
                    "required": True,
                    "schema": {
                        "type": "object",
                        "default": example,
                        "example": example,
                    },
                }
            )
        return path, value


class AddParametersOnContent(RequestHookBase):
    def hook(self, path: str, value: dict):
        path, value = super().hook(path, value)
        for key in self.PLACEHOLDER[self.path_name].keys():
            value["parameters"].append(
                {
                    "name": key,
                    "in": "query",
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": self.placeholder_to_yaml(
                                self.PLACEHOLDER[self.path_name][key]
                            ),
                        },
                    },
                }
            )
        return path, value


class AddParametersOnParameters(RequestHookBase):
    def hook(self, path: str, value: dict):
        path, value = super().hook(path, value)
        for key in self.PLACEHOLDER[self.path_name].keys():
            value["parameters"].append(
                {
                    "name": key,
                    "in": "query",
                    "required": True,
                    "schema": self.placeholder_to_yaml(
                        self.PLACEHOLDER[self.path_name][key]
                    ),
                }
            )
        return path, value


class AddParametersOnBody(RequestHookBase):
    def hook(self, path: str, value: dict):
        path, value = super().hook(path, value)
        data = self.PLACEHOLDER[self.path_name]
        schema = {i: self.placeholder_to_yaml(data[i]) for i in data.keys()}
        value["requestBody"] = {
            "description": "body",
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "properties": schema,
                    },
                }
            },
        }
        return path, value
