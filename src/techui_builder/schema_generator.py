import json
import logging
from pathlib import Path

import typer

from techui_builder.models import (
    GuiComponents,
    TechUi,
)

SCHEMAS_DIR = Path("schemas")

logger_ = logging.getLogger(__name__)

app = typer.Typer(context_settings={"allow_interspersed_args": True})


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
    if not SCHEMAS_DIR.exists():
        try:
            SCHEMAS_DIR.mkdir()
        except OSError:
            logger_.critical("Unable to make schemas dir.")
            exit()

    # techui
    tu = TechUi.model_json_schema()
    write_json_schema("techui", tu)

    # ibek_mapping
    tu_support = GuiComponents.model_json_schema()
    write_json_schema("techui.support", tu_support)
