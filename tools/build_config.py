from hooks import (
    AddParametersOnBody,
    AddParametersOnContent,
    AddParametersOnParameters,
    AddPathQueryIdOnParameters,
    RemoveErrorHandle,
    SetResponsesHeader,
)


class Config:
    OUTPUT_DIR = "dist/{0}"
    INPUT_DIR = "src/openapi"

    def hooks_generator(
        self,
        queryParameterJson=True,
        removeLegacyDiscriminatorBehavior=False,
    ):
        # https://stackoverflow.com/questions/34820064/defining-an-api-with-swagger-get-call-that-uses-json-in-parameters/45223964
        if queryParameterJson:
            # ["parameters"][0]["content"]["application/json"]["schema"]
            getParamHook = AddParametersOnContent(
                split=-1,
                contentType="application/json",
                ignoreKeys=["queryId"],
            )
        else:
            # ["parameters"][0]["schema"]
            getParamHook = AddParametersOnParameters(
                split=-1,
                schemaType="string",
                ignoreKeys=["queryId"],
            )

        # https://github.com/OpenAPITools/openapi-generator/issues/15373
        additionalHooks = []
        if removeLegacyDiscriminatorBehavior:
            additionalHooks.append(RemoveErrorHandle())

        return {
            "openapi": [],
            "schemas": [],
            "other": [],
            "request": {
                key: [
                    SetResponsesHeader(),
                    AddPathQueryIdOnParameters(split=-1),
                    getParamHook,
                    *additionalHooks,
                ]
                for key in ["default", "user", "users", "user-list", "tweet"]
            }
            | {
                key: [
                    SetResponsesHeader(),
                    AddPathQueryIdOnParameters(split=-1),
                    AddParametersOnBody(
                        split=-1,
                        schemaType=None,
                        contentType="application/json",
                    ),
                    *additionalHooks,
                ]
                for key in ["post"]
            }
            | {
                key: [
                    SetResponsesHeader(),
                    AddParametersOnParameters(split=2, schemaType=None),
                ]
                for key in ["v1.1-get", "v2.0-get"]
            }
            | {
                key: [
                    SetResponsesHeader(),
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
            "compatible": self.hooks_generator(
                queryParameterJson=False,
            ),
            "compatible_discriminator": self.hooks_generator(
                queryParameterJson=False,
                removeLegacyDiscriminatorBehavior=True,
            ),
        }
