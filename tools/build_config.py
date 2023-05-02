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
                    "v1.1": [SetResponsesHeader()],
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
                    "v1.1": [SetResponsesHeader()],
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
                    "v1.1": [SetResponsesHeader()],
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
                    "v1.1": [SetResponsesHeader()],
                },
            },
        }

        """
    "docs": {
        "header": "securitySchemes",
        "get_parameters": "schema_content",
        "post_parameters": "schema_parameters"
    },
    "dart": {
        "header": "parameters",
        "get_parameters": "string",
        "post_parameters": "object"
    },
    "typescript": {
        "header": "securitySchemes",
        "get_parameters": "string",
        "post_parameters": "object"
    },
    "test": {
        "header": "securitySchemes",
        "get_parameters": "string",
        "post_parameters": "string"
    }
    """
