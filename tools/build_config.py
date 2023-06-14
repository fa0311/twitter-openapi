from hooks import *


class Config:
    OUTPUT_DIR = "dist/{0}"
    INPUT_DIR = "src/openapi"

    def hooks_generator(self, queryParameterJson=True):
        # https://stackoverflow.com/questions/34820064/defining-an-api-with-swagger-get-call-that-uses-json-in-parameters/45223964
        if queryParameterJson:
            getParamHook = AddParametersOnContent(
                split=-1,
                contentType="application/json",
                ignoreKeys=["queryId"],
            )
            postParamHook = AddParametersOnParameters(
                split=-1,
                schemaType=None,
            )
        else:
            getParamHook = AddParametersOnParameters(
                split=-1,
                schemaType="string",
                ignoreKeys=["queryId"],
            )
            postParamHook = AddParametersOnBody(
                split=-1,
                schemaType=None,
                contentType="application/json",
            )

        return {
            "openapi": [AddSecuritySchemesOnSecuritySchemes()],
            "schemas": [],
            "other": [],
            "request": {
                key: [
                    SetResponsesHeader(suffix=None),
                    AddPathQueryIdOnParameters(split=-1),
                    getParamHook,
                ]
                for key in ["default", "user", "user-list", "tweet"]
            }
            | {
                key: [
                    SetResponsesHeader(suffix=None),
                    AddPathQueryIdOnParameters(split=-1),
                    postParamHook,
                ]
                for key in ["post"]
            }
            | {
                key: [
                    SetResponsesHeader(suffix="legacy"),
                    AddParametersOnParameters(split=2, schemaType=None),
                ]
                for key in ["v1.1-get", "v2.0-get"]
            }
            | {
                key: [
                    SetResponsesHeader(suffix="legacy"),
                    AddParametersOnBody(
                        split=2,
                        schemaType=None,
                        contentType="application/x-www-form-urlencoded",
                    ),
                ]
                for key in ["v1.1-post", "v2.0-post"]
            }
            | {"other": []},
        }

    def main(self):
        return {
            "docs": self.hooks_generator(),
            "compatible": self.hooks_generator(queryParameterJson=False),
        }
