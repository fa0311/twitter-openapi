import glob

for file in glob.glob("python_generated/openapi_client/models/*.py"):
    with open(file, "r") as f:
        text = f.read()

    indent = "    "

    text = text.replace(
        f"{indent}{indent}try:",
        f"{indent}{indent}if match == 0:",
    )
    text = text.replace(
        f"{indent}{indent}except (ValidationError, ValueError) as e:",
        f"{indent}{indent}else:",
    )
    text = text.replace(
        f"{indent}{indent}{indent}error_messages.append(str(e))",
        f"{indent}{indent}{indent}pass",
    )

    with open(file, "w") as f:
        f.write(text)
