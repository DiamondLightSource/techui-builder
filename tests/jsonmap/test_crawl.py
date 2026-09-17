from pathlib import Path

import pytest

from techui_builder.jsonmap.crawl import CrawlContext, crawl, crawl_link
from techui_builder.jsonmap.links import WidgetLink, WidgetType
from techui_builder.jsonmap.nodes import ScreenNode


@pytest.fixture
def t01_ctx(json_map_generator) -> CrawlContext:
    synoptic = json_map_generator.bob_path.parent
    return CrawlContext(
        components=json_map_generator.techui_yaml.components,
        synoptic_dir=synoptic,
        link_base_dir=synoptic,
        component_name=None,
        service_name="",
    )


def test_crawl(t01_ctx):
    json_map = crawl(t01_ctx.synoptic_dir / "index.bob", t01_ctx)

    assert json_map.file == "index.bob"
    assert json_map.display_name == "Display"
    assert json_map.error == ""
    assert [(c.file, c.display_name, c.exists) for c in json_map.children] == [
        ("dcam1.bob", "Diagnostic Camera 1", True),
        ("test.bob", "Diode 1", False),
        ("temp1.bob", "Temperaure Controller 1", False),
        ("motor1.bob", "Motor Stage", True),
    ]


def test_crawl_component_screen(t01_ctx):
    motor = crawl(t01_ctx.synoptic_dir / "motor1.bob", t01_ctx, link_name="motor1")

    assert motor.display_name == "Motor Stage"
    assert [(c.file, c.display_name) for c in motor.children] == [
        ("../bl01t-mo-motor-01/pmacAxis.pvi.bob", "X1"),
        ("../bl01t-mo-motor-01/pmacAxis.pvi.bob", "A"),
        ("techui-support/bob/pmac/pmacController.bob", "pmacController"),
    ]


def test_crawl_link(t01_ctx):
    found = crawl_link(
        WidgetLink("motor1.bob", "motor1", WidgetType.ACTION_BUTTON, {}),
        "Motor Stage",
        t01_ctx,
    )
    missing = crawl_link(
        WidgetLink("missing.bob", "Missing", WidgetType.ACTION_BUTTON, {}),
        "Missing",
        t01_ctx,
    )

    assert found.file == "motor1.bob"
    assert len(found.children) == 3
    assert missing == ScreenNode("missing.bob", "Missing", exists=False)


def test_with_screen_component(t01_ctx):
    motor_ctx = t01_ctx.with_screen_component(Path("motor1.bob"))

    assert motor_ctx.component_name == "motor1"
    assert motor_ctx.service_name == "bl01t-mo-motor-01"
    # Not a component
    assert t01_ctx.with_screen_component(Path("index.bob")) is t01_ctx
    # Already inside a component
    assert motor_ctx.with_screen_component(Path("dcam1.bob")) is motor_ctx
