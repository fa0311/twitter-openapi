from hooks import *


class Config:
    OUTPUT_DIR = "dist/{0}"
    INPUT_DIR = "src/openapi"

    def main(self):
        return {
            "docs": {
                "openapi": [AddSecuritySchemesOnSecuritySchemes()],
                "request": {
                    key: [
                        ReplaceQueryIdPlaceholder(split=-1),
                        SetResponsesHeader(suffix=None),
                        AddParametersOnContent(split=-1),
                    ]
                    for key in ["default", "user", "user-list", "tweet"]
                }
                | {
                    key: [
                        ReplaceQueryIdPlaceholder(split=-1),
                        SetResponsesHeader(suffix=None),
                        AddParametersOnParameters(split=-1),
                    ]
                    for key in ["post"]
                }
                | {
                    key: [
                        SetResponsesHeader("legacy"),
                        AddParametersOnParameters(split=2),
                    ]
                    for key in ["v1.1-get", "v1.1-post", "v2.0-get", "v2.0-post"]
                },
            },
            "dart": {
                "openapi": [],
                "request": {
                    key: [
                        ReplaceQueryIdPlaceholder(split=-1),
                        AddSecuritySchemesOnHeader(split=-1),
                        SetResponsesHeader(suffix=None),
                        AddParametersOnParametersAsString(split=-1),
                    ]
                    for key in ["default", "user", "user-list", "tweet"]
                }
                | {
                    key: [
                        ReplaceQueryIdPlaceholder(split=-1),
                        AddSecuritySchemesOnHeader(split=-1),
                        SetResponsesHeader(suffix=None),
                        AddParametersOnBody(split=-1),
                    ]
                    for key in ["post"]
                }
                | {
                    key: [
                        SetResponsesHeader(suffix="legacy"),
                        AddParametersOnParametersAsString(split=2),
                    ]
                    for key in ["v1.1-get", "v2.0-get"]
                }
                | {
                    key: [
                        SetResponsesHeader(suffix="legacy"),
                        AddParametersOnBody(split=2),
                    ]
                    for key in ["v1.1-post", "v2.0-post"]
                },
            },
            "typescript": {
                "openapi": [AddSecuritySchemesOnSecuritySchemes()],
                "request": {
                    key: [
                        ReplaceQueryIdPlaceholder(split=-1),
                        SetResponsesHeader(suffix=None),
                        AddParametersOnParametersAsString(split=-1),
                    ]
                    for key in ["default", "user", "user-list", "tweet"]
                }
                | {
                    key: [
                        ReplaceQueryIdPlaceholder(split=-1),
                        SetResponsesHeader(suffix=None),
                        AddParametersOnParametersAsObject(split=-1),
                    ]
                    for key in ["post"]
                }
                | {
                    key: [
                        SetResponsesHeader(suffix="legacy"),
                        AddParametersOnParametersAsObject(split=2),
                    ]
                    for key in ["v1.1-get", "v1.1-post", "v2.0-get", "v2.0-post"]
                },
            },
            "test": {
                "openapi": [AddSecuritySchemesOnSecuritySchemes()],
                "request": {
                    key: [
                        ReplaceQueryIdPlaceholder(split=-1),
                        SetResponsesHeader(suffix=None),
                        AddParametersOnParametersAsString(split=-1),
                    ]
                    for key in ["default", "user", "user-list", "tweet"]
                }
                | {
                    key: [
                        ReplaceQueryIdPlaceholder(split=-1),
                        SetResponsesHeader(suffix=None),
                        AddParametersOnParametersAsString(split=-1),
                    ]
                    for key in ["post"]
                }
                | {
                    key: [
                        SetResponsesHeader(suffix="legacy"),
                        AddParametersOnParametersAsObject(split=2),
                    ]
                    for key in ["v1.1-get", "v1.1-post", "v2.0-get", "v2.0-post"]
                },
            },
        }
