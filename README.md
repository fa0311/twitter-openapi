# Twitter OpenAPI

Twitter OpenAPI(Swagger) specification

- [Dart](https://github.com/fa0311/twitter_openapi_dart)
- [TypeScript](https://github.com/fa0311/twitter-openapi-typescript)
- [React Documents](https://github.com/fa0311/twitter-openapi-docs)

## Usage

```shell
openapi-generator-cli generate -g <language> -i https://raw.githubusercontent.com/fa0311/twitter-openapi/main/dist/docs/openapi-3.0.yaml -o ./generated
```

There are several outputs, but the one that best follows the OpenAPI specification is `dist/docs`.  
However, some Generators may use a syntax that is not supported.  
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

[agpl-3.0](./LICENSE.txt)

aa
