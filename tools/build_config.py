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
                        ReplaceQueryIdPlaceholder(),
                        SetResponsesHeader(),
                        AddParametersOnContent(),
                    ]
                    for key in ["default", "user", "userList", "tweet"]
                }
                | {
                    "post": [
                        ReplaceQueryIdPlaceholder(),
                        SetResponsesHeader(),
                        AddParametersOnParameters(),
                    ],
                    "v1.1": [SetResponsesHeader("v1.1"), AddParametersOnParameters()],
                },
            },
            "dart": {
                "openapi": [],
                "request": {
                    key: [
                        ReplaceQueryIdPlaceholder(),
                        AddSecuritySchemesOnHeader(),
                        SetResponsesHeader(),
                        AddParametersOnParametersAsString(),
                    ]
                    for key in ["default", "user", "userList", "tweet"]
                }
                | {
                    "post": [
                        ReplaceQueryIdPlaceholder(),
                        AddSecuritySchemesOnHeader(),
                        SetResponsesHeader(),
                        AddParametersOnParametersAsObject(),
                    ],
                    "v1.1": [
                        SetResponsesHeader("v1.1"),
                        AddParametersOnParametersAsObject(),
                    ],
                },
            },
            "typescript": {
                "openapi": [AddSecuritySchemesOnSecuritySchemes()],
                "request": {
                    key: [
                        ReplaceQueryIdPlaceholder(),
                        SetResponsesHeader(),
                        AddParametersOnParametersAsString(),
                    ]
                    for key in ["default", "user", "userList", "tweet"]
                }
                | {
                    "post": [
                        ReplaceQueryIdPlaceholder(),
                        SetResponsesHeader(),
                        AddParametersOnParametersAsObject(),
                    ],
                    "v1.1": [
                        SetResponsesHeader("v1.1"),
                        AddParametersOnParametersAsObject(),
                    ],
                },
            },
            "test": {
                "openapi": [AddSecuritySchemesOnSecuritySchemes()],
                "request": {
                    key: [
                        ReplaceQueryIdPlaceholder(),
                        SetResponsesHeader(),
                        AddParametersOnParametersAsString(),
                    ]
                    for key in ["default", "user", "userList", "tweet"]
                }
                | {
                    "post": [
                        ReplaceQueryIdPlaceholder(),
                        SetResponsesHeader(),
                        AddParametersOnParametersAsString(),
                    ],
                    "v1.1": [
                        SetResponsesHeader("v1.1"),
                        AddParametersOnParametersAsString(),
                    ],
                },
            },
        }
