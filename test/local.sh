

python3 tools/build.py
java -jar openapi-generator-cli.jar generate -c test/python/openapi-generator-config.yaml -g python
python3 -m pip install ./python_generated
python3 test/python/test_serialize.py