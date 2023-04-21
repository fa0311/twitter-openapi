# Twitter OpenAPI

Twitter OpenAPI(Swagger) specification

- [Dart](https://github.com/fa0311/twitter_openapi_dart)
- [React Documents](https://github.com/fa0311/twitter-openapi-docs)

## Usage

```shell
openapi-generator-cli generate -g <language> -i https://raw.githubusercontent.com/fa0311/twitter-openapi/main/dist/openapi-3.0.yaml -o ./generated
```

Note that the license also inherits to the output.

## Contribute

- `src` *.yaml files should be written according to the [v3.0/schema.json](https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/schemas/v3.0/schema.json)
- `dist` Do not rewrite this file as it is an automatically generated OpenAPI file.

### About build

- `src/openapi/**/*.yaml#/paths/*/get/parameters` will be overwritten by `src/config/parameters.yaml#/paths/~1parameters/get/parameters`
- `src/openapi/**/*.yaml#/paths/*/get/responses/200/headers` will be overwritten by `src/config/headers.yaml#/components/headers`

```shell
python -V # Python 3.10.8
pip install -r requirements.txt
python tools/build.py
```

## License

[agpl-3.0](./LICENSE.txt)
