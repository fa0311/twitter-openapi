# Twitter OpenAPI

Twitter OpenAPI(Swagger) specification

- [Dart](https://github.com/fa0311/twitter_openapi_dart)
- [React Documents](https://github.com/fa0311/twitter-openapi-docs)

## Usage

```shell
openapi-generator-cli generate -g <language> -i https://raw.githubusercontent.com/fa0311/twitter-openapi/main/dist/typescript/openapi-3.0.yaml -o ./generated
```

If the language supports variable-length arguments.

```shell
openapi-generator-cli generate -g <language> -i https://raw.githubusercontent.com/fa0311/twitter-openapi/main/dist/dart/openapi-3.0.yaml -o ./generated
```

Note that the license also inherits to the output.

## Contribute

- `src` *.yaml files should be written according to the [v3.0/schema.json](https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/schemas/v3.0/schema.json)
- `dist` Do not rewrite this file as it is an automatically generated OpenAPI file.

### About build

- `src/openapi/**/*.yaml#/paths/*/*/parameters` will be overwritten by `src/config/parameters.yaml#/paths/~1parameters/*/parameters`
  - This overwritten done before parsing yaml
- `src/openapi/**/*.yaml#/paths/*/*/requestBody` will be overwritten by `src/config/parameters.yaml#/paths/~1parameters/*/requestBody`
  - This overwritten done before parsing yaml
- `src/openapi/**/*.yaml#/paths/*/get/responses/200/headers` will be overwritten by `src/config/headers.yaml#/components/headers`
  - This overwritten done before parsing yaml
- Items enclosed in double brackets are placeholders
  - `src/config/placeholder.json` replaces it
  - If a placeholder is used in `src/config/**/*.yaml`, the pathname is added as a prefix
  - This substitution is done before parsing the yaml

#### variable.json

It can be written as `{% if variable == value %}` `{ endif }`

| lang | description|
|---|---|
| docs | Outputs the most correct swagger syntax |
| typescript | Since it is difficult to handle default values with the typescript generator, we refer to `src/config/placeholder.json` and handle default values |
| dart | Basically the same as typescript, but headers are processed as parameters |

##### *_parameters = string

- This is defined in `src/config/parameters.yaml`
- Replace `src/config/placeholder.json` as an string

##### *_parameters = object

- This is defined in `src/config/parameters.yaml`
- Replace `src/config/placeholder.json` as an object

##### *_parameters = schema_content

- The schema automatically generated from the `src/config/placeholder.json` is replaced with `src/openapi/**/*.yaml#/paths/*/*/parameters`
- Some generators cannot handle it correctly because it generates the syntax introduced in swagger 3.0
- This is defined in `tools/build.py`

##### *_parameters = schema_parameters

- The schema automatically generated from the `src/config/placeholder.json` is replaced with `src/openapi/**/*.yaml#/paths/*/*/parameters`

##### *_parameters = schema_request_body

- The schema automatically generated from the `src/config/placeholder.json` is replaced with `src/openapi/**/*.yaml#/paths/*/*/requestBody`

#### command

```shell
python -V # Python 3.10.8
pip install -r requirements.txt
python tools/build.py
```

## License

[agpl-3.0](./LICENSE.txt)
