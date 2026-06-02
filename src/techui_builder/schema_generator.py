import json
from pathlib import Path

import typer

from techui_builder.models import (
    GuiComponents,
    TechUi,
)

SCHEMAS_DIR = Path("schemas")
SCHEMAS_DIR.mkdir(exist_ok=True)

app = typer.Typer()


def write_json_schema(model_name: str, schema_dict: dict) -> None:
    out = SCHEMAS_DIR / f"{model_name}.schema.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(schema_dict, f, sort_keys=False)
    print(f"✅ Wrote {out}")


@app.callback(
    help="Generate schema for validating techui and ibek-mapping yaml files",
    invoke_without_command=True,
)
def schema_generator() -> None:
    # techui
    tu = TechUi.model_json_schema()
    write_json_schema("techui", tu)

    # ibek_mapping
    tu_support = GuiComponents.model_json_schema()
    write_json_schema("techui.support", tu_support)
