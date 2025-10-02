from __future__ import annotations

from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from techui_builder.models import TechUi


def _validate_json_schema(schema_path: Path, data: dict) -> None:
    import yaml as _yaml

    with schema_path.open("r", encoding="utf-8") as sf:
        schema = _yaml.safe_load(sf)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        msgs = "\n".join(
            f" - At {'/'.join(map(str, e.path)) or '(root)'}: {e.message}"
            for e in errors
        )
        raise ValueError(f"Schema validation failed for {schema_path.name}:\n{msgs}")


def load_tech_ui(path: Path, schema_path: Path | None = None) -> TechUi:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if schema_path:
        _validate_json_schema(schema_path, data)
    return TechUi.model_validate(data)


def load_all(
    tech_ui_path: Path,
    tech_ui_schema: Path | None = None,
) -> TechUi:
    tu = load_tech_ui(tech_ui_path, tech_ui_schema)

    return tu
