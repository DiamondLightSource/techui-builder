from __future__ import annotations

from pathlib import Path

import yaml

from techui_builder.models import (
    GuiComponents,
    TechUi,
)

SCHEMAS_DIR = Path("schemas")
SCHEMAS_DIR.mkdir(exist_ok=True)


def write_yaml_schema(model_name: str, schema_dict: dict) -> None:
    out = SCHEMAS_DIR / f"{model_name}.schema.yml"
    with out.open("w", encoding="utf-8") as f:
        yaml.safe_dump(schema_dict, f, sort_keys=False)
    print(f"✅ Wrote {out}")


def patch_tech_ui(schema: dict) -> dict:
    """
    Add propertyNames pattern for components dict.
    """
    props = schema.get("properties", {})
    components = props.get("components")
    if isinstance(components, dict):
        # Ensure object type and add a key-name restriction
        components.setdefault("type", "object")
        components["propertyNames"] = {"type": "string", "pattern": r"^[A-Z0-9_]+$"}
    return schema


def patch_gui_components(schema: dict) -> dict:
    # Root dict → patternProperties + add $schema + additionalProperties: false
    if schema.get("type") == "object" and "additionalProperties" in schema:
        entry_schema = schema["additionalProperties"]
        schema.setdefault("properties", {})
        schema["properties"]["$schema"] = {"type": "string"}
        schema["patternProperties"] = {
            r"^[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+$": entry_schema
        }
        schema["additionalProperties"] = False

    # Add second pattern to require at least one $(NAME) macro
    defs = schema.get("$defs") or schema.get("definitions") or {}
    gce = defs.get("GuiComponentEntry") or {}
    props = gce.get("properties") or {}
    prefix = props.get("prefix")
    if isinstance(prefix, dict):
        allowed = prefix.copy()
        # normalize to a clean allOf form
        pattern_allowed = allowed.get("pattern", r"^[A-Za-z0-9_:\-./\s\$\(\)]+$")
        prefix.clear()
        prefix["allOf"] = [
            {"type": "string", "pattern": pattern_allowed},
            {"type": "string", "pattern": r"\$\([A-Za-z][A-Za-z0-9_]*\)"},
        ]
    return schema


def main() -> None:
    # CreateGui
    cg = TechUi.model_json_schema(ref_template="#/$defs/{model}")
    cg.setdefault("$schema", "https://json-schema.org/draft/2020-12/schema")
    cg = patch_tech_ui(cg)
    write_yaml_schema("techui", cg)

    # GuiComponents (Cameras/Motion/Vacuum registry)
    gcomp = GuiComponents.model_json_schema(ref_template="#/$defs/{model}")
    gcomp.setdefault("$schema", "https://json-schema.org/draft/2020-12/schema")
    gcomp = patch_gui_components(gcomp)
    write_yaml_schema("ibek_mapping", gcomp)


if __name__ == "__main__":
    main()
