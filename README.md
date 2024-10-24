# Twitter OpenAPI

Twitter OpenAPI(Swagger) specification

[issues](https://github.com/fa0311/twitter-openapi/issues) / [discussions](https://github.com/fa0311/twitter-openapi/discussions)

- [Python](https://github.com/fa0311/twitter_openapi_python)
- [Dart](https://github.com/fa0311/twitter_openapi_dart)
- [TypeScript](https://github.com/fa0311/twitter-openapi-typescript)
- [React Documents](https://github.com/fa0311/twitter-openapi-docs)

## Usage

```shell
openapi-generator-cli generate -g <language> -i https://raw.githubusercontent.com/fa0311/twitter-openapi/main/dist/docs/openapi-3.0.yaml -o ./generated
```

There are several outputs, but the one that best follows the OpenAPI specification is `dist/docs`.  
However, some Generators may use a syntax that is not supported.  

There are several outputs, but the one that most closely follows the OpenAPI specification is `dist/docs`.
However, a lot of syntax that is not supported by some generators is used.
Therefore, it is recommended to use `dist/compatible` or `dist/compatible_discriminator`.

You can also modify the hook to make the generated results more user-friendly. [build_config.py](./tools/build_config.py)  

Note that the license also inherits to the output.

## Contribute

[CONTRIBUTING.md](./CONTRIBUTING.md)

### build

```shell
python -V # Python 3.10.8
pip install -r requirements.txt
python tools/build.py
```

## License

This project is dual licensed. You can choose one of the following licenses:

- [Custom License](./LICENSE)
- [GNU Affero General Public License v3.0](./LICENSE.AGPL)
