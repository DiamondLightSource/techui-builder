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


def main() -> None:
    # CreateGui
    cg = TechUi.model_json_schema()
    write_yaml_schema("techui", cg)

    # GuiComponents (Cameras/Motion/Vacuum registry)
    gcomp = GuiComponents.model_json_schema()
    write_yaml_schema("ibek_mapping", gcomp)


if __name__ == "__main__":
    main()
