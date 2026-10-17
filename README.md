# Twitter OpenAPI

Twitter OpenAPI(Swagger) specification

[issues](https://github.com/fa0311/twitter-openapi/issues) / [discussions](https://github.com/fa0311/twitter-openapi/discussions)

- [Python](https://github.com/fa0311/twitter_openapi_python)
- [Dart](https://github.com/fa0311/twitter_openapi_dart)
- [TypeScript](https://github.com/fa0311/twitter-openapi-typescript)
- [React Documents](https://github.com/fa0311/twitter-openapi-docs)
- [HTTP relay](https://github.com/fa0311/twitter_api_safe_relay) runs requests through a logged-in browser; the generated clients can be pointed at it

## Usage

```shell
openapi-generator-cli generate -g <language> -i https://raw.githubusercontent.com/fa0311/twitter-openapi/main/dist/docs/openapi-3.0.yaml -o ./generated
```

There are several outputs, but the one that most closely follows the OpenAPI specification is `dist/docs`.
However, a lot of syntax that is not supported by some generators is used.

You can also modify the hook to make the generated results more user-friendly. [build_config.py](./tools/build_config.py)

Note that the license also inherits to the output.

## Contribute

[CONTRIBUTING.md](./CONTRIBUTING.md)

### build

```shell
uv run python tools/build.py
```

### update placeholder.json

```shell
uv run tools/update_placeholder.py https://raw.githubusercontent.com/fa0311/twitter_api_safe_relay/main/packages/server/requests.ndjson
```

### test

```shell
java -jar openapi-generator-cli.jar generate -c test/python/openapi-generator-config.yaml -g python
uv pip install ./python_generated
STRICT_MODE=True uv run python test/python/test_serialize.py  # needs cookie.json
```

## License

This project is dual licensed. You can choose one of the following licenses:

- [Custom License](./LICENSE)
- [GNU Affero General Public License v3.0](./LICENSE.AGPL)
