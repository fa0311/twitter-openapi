# CONTRIBUTING

- `src` *.yaml files should be written according to the [v3.0/schema.json](https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/schemas/v3.0/schema.json)
- `dist` Do not rewrite this file as it is an automatically generated OpenAPI file.
- `dist` Do not include this in the pull request due to potential conflicts.

Users using vscode can build and test with the GUI.
[.vscode/launch.json](.vscode/launch.json) is a configuration file for vscode.

## Enum or plain string

X keeps adding values to many fields, and the generated clients reject an enum value they do not know (Python raises while deserializing the whole response). Decide per field:

- `enum` when the value decides the shape of the data or the branch a client takes (`__typename`, `itemType`, `*Ref.type`, `cursorType`, `urlType`, `media.type`, binding value `type`), or when it is user-facing and a closed set (`limited_actions[].action`, `conversation_control.policy`, `verified_type`, `profile_image_shape`, `richtext_types`, `views.state`, ...). A new value should fail loudly in the strict test and be added the same day. twitter-snap is the reference consumer: anything a renderer branches on belongs here.
- plain `string` when the value is UI plumbing that changes nothing structurally (icon names, feedback kinds, prompt and cover display styles, `reason` on community action results, ...). Keep the known values in a comment next to the field.

Only values recorded from the real frontend go into an enum; never guess one.

## Good first issues

- Add a new endpoint
- Add type to `type: object # todo`
