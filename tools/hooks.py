import yaml
import json


class HookBase:
    PLACEHOLDER: dict

    def __init__(self):
        with open("src/config/placeholder.json", mode="r", encoding="utf-8") as f:
            self.PLACEHOLDER = json.load(f)

    def placeholder_to_yaml(self, obj, default=False, example=False) -> dict:
        def mine(x):
            return self.placeholder_to_yaml(x, default=default, example=example)

        def fn(x: str):
            return x[:-1] if x.endswith("?") else x

        if isinstance(obj, dict):
            req = {k: v for k, v in obj.items() if not k.endswith("?")}
            properties = {fn(k): mine(v) for k, v in obj.items()}
            value = {
                "type": "object",
                "properties": properties,
            }
            value.update({"required": [i for i in req]} if len(req) > 0 else {})
            value.update({"default": properties} if default else {})
            value.update({"example": properties} if example else {})
            return value
        elif isinstance(obj, list) and len(obj) > 0:
            properties = mine(obj[0])
            value = {
                "type": "array",
                "items": properties,
            }
            value.update({"default": [properties]} if default else {})
            value.update({"example": [properties]} if example else {})
            return value
        elif isinstance(obj, list) and len(obj) == 0:
            value = {
                "type": "array",
                "items": {"type": "object"},
            }
            value.update({"default": []} if default else {})
            value.update({"example": []} if example else {})
            return value
        elif isinstance(obj, str):
            return {"type": "string", "example": obj, "default": obj}
        elif isinstance(obj, bool):
            return {"type": "boolean", "example": obj, "default": obj}
        elif isinstance(obj, int):
            return {"type": "integer", "example": obj, "default": obj}

    def load_component(self, name: str) -> dict:
        with open(f"src/config/component/{name}.yaml", mode="r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_placeholder(self) -> dict:
        with open("src/config/placeholder.json", mode="r", encoding="utf-8") as f:
            return yaml.safe_load(f)


# HookBase extends


class OpenapiHookBase(HookBase):
    def hook(self, value: dict) -> dict:
        return value


class OtherHookBase(HookBase):
    def hook(self) -> tuple[str, dict]:
        return "", {}


class SchemasHookBase(HookBase):
    def hook(self, value: dict) -> dict:
        return value


class RequestHookBase(HookBase):
    split: int
    path_name: str

    def __init__(self, split=1):
        super().__init__()
        self.split = split

    def hook(self, path: str, value: dict) -> tuple[str, dict]:
        value["parameters"] = value.get("parameters", [])
        self.path_name = "/".join(path.split("/")[self.split :])
        return path, value


# OpenapiHookBase extends


class AddSecuritySchemesOnSecuritySchemes(OpenapiHookBase):
    def hook(self, value: dict):
        value = super().hook(value)
        component = self.load_component("security_schemes")
        param = component["components"]["securitySchemes"]
        value["components"]["securitySchemes"].update(param)
        value["security"].extend(component["security"])
        return value


# SchemasHookBase extends


class RemoveDiscriminator(SchemasHookBase):
    def hook(self, value: dict):
        if value.get("discriminator") is not None:
            del value["discriminator"]
        return value


class SchemasCheck(SchemasHookBase):
    def hook(self, value: dict):
        if value.get("allOf") is not None:
            print("allOf is used")
        if value.get("type") is None:
            print("Type is None")
        return value


class RequiredCheck(SchemasHookBase):
    def hook(self, value: dict):
        required = value.get("required", [])

        for key, property in value.get("properties", {}).items():
            if key in required and property.get("default") is not None:
                print(f"{key} is required and has default value")
            d = property.get("default") is None and property.get("nullable", False)
            if property not in required and d:
                print(f"{key} is not required and has no default value")

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
        return path.replace(r"{pathQueryId}", new), value


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


class AddPathQueryIdOnParameters(RequestHookBase):
    def __init__(self, split: str = 1):
        super().__init__(split=split)

    def hook(self, path: str, value: dict):
        path, value = super().hook(path, value)
        data = self.PLACEHOLDER[self.path_name]
        value["parameters"].append(
            {
                "in": "path",
                "name": "pathQueryId",
                "required": True,
                "schema": {
                    "type": "string",
                    "default": data["queryId"],
                    "example": data["queryId"],
                },
            }
        )
        return path, value


# OnParameters


class AddParametersOnParameters(RequestHookBase):
    schemaType: str | None
    ignoreKeys: list[str]

    def __init__(
        self,
        split: str = 1,
        schemaType: str | None = None,
        ignoreKeys: list[str] | None = None,
    ):
        super().__init__(split=split)
        self.schemaType = schemaType
        self.ignoreKeys = ignoreKeys or []

    def hook(self, path: str, value: dict):
        path, value = super().hook(path, value)
        data = self.PLACEHOLDER[self.path_name]
        data = {key: data[key] for key in data.keys() if key not in self.ignoreKeys}

        for key in data.keys():
            if self.schemaType == "string":
                example = (
                    data[key] if isinstance(data[key], str) else json.dumps(data[key])
                )
                schema = {
                    "type": "string",
                    "default": example,
                    "example": example,
                }
            elif self.schemaType == "object":
                example = (
                    data[key] if isinstance(data[key], str) else json.dumps(data[key])
                )
                schema = {
                    "type": "object",
                    "default": example,
                    "example": example,
                }
            else:
                schema = self.placeholder_to_yaml(data[key])
            value["parameters"].append(
                {
                    "name": key,
                    "in": "query",
                    "required": True,
                    "schema": schema,
                }
            )
        return path, value


# OnBody


class AddParametersOnBody(RequestHookBase):
    schemaType: str | None
    contentType: str | None
    ignoreKeys: list[str]

    def __init__(
        self,
        split: str = 1,
        contentType: str = "application/json",
        schemaType: str | None = None,
        ignoreKeys: list[str] | None = None,
    ):
        super().__init__(split)
        self.schemaType = schemaType
        self.contentType = contentType
        self.ignoreKeys = ignoreKeys or []

    def hook(self, path: str, value: dict):
        path, value = super().hook(path, value)
        data: dict[str, dict] = self.PLACEHOLDER[self.path_name]
        data = {k: v for k, v in data.items() if k not in self.ignoreKeys}

        if self.schemaType == "string":
            example = data if isinstance(data, str) else json.dumps(data)
            schema = {
                "type": "string",
                "default": example,
                "example": example,
            }
        elif self.schemaType == "object":
            example = data if isinstance(data, str) else json.dumps(data)
            schema = {
                "type": "object",
                "default": example,
                "example": example,
            }
        else:
            schema = {
                "properties": {k: self.placeholder_to_yaml(v) for k, v in data.items()},
                "required": [k for k in data.keys()],
            }
        value["requestBody"] = {
            "description": "body",
            "required": True,
            "content": {
                self.contentType: {
                    "schema": schema,
                }
            },
        }
        return path, value


# OnContent


class AddParametersOnContent(RequestHookBase):
    contentType: str
    ignoreKeys: list[str]

    def __init__(
        self,
        split: str = 1,
        contentType: str = "application/json",
        ignoreKeys: list[str] | None = None,
    ):
        super().__init__(split=split)
        self.contentType = contentType
        self.ignoreKeys = ignoreKeys or []

    def hook(self, path: str, value: dict):
        path, value = super().hook(path, value)
        data = self.PLACEHOLDER[self.path_name]
        data = {key: data[key] for key in data.keys() if key not in self.ignoreKeys}

        for key in data.keys():
            value["parameters"].append(
                {
                    "name": key,
                    "in": "query",
                    "required": True,
                    "content": {
                        self.contentType: {
                            "schema": self.placeholder_to_yaml(data[key]),
                        }
                    },
                }
            )
        return path, value
