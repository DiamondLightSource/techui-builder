from pathlib import Path

import pytest

from techui_builder.jsonmap.crawl import CrawlContext, crawl, crawl_link
from techui_builder.jsonmap.fetch import ScreenFetcher
from techui_builder.jsonmap.links import WidgetLink, WidgetType
from techui_builder.jsonmap.nodes import ScreenNode

MOTOR_IOC = "https://t01-opis.diamond.ac.uk/bl01t-mo-motor-01"
DCAM_IOC = "https://b01-1-opis.diamond.ac.uk/bl01c-di-dcam-01"


@pytest.fixture
def t01_ctx(json_map_generator) -> CrawlContext:
    synoptic = json_map_generator.bob_path.parent
    return CrawlContext(
        components=json_map_generator.techui_yaml.components,
        synoptic_dir=synoptic,
        fetcher=ScreenFetcher(),
        component_name=None,
        screen=synoptic / "index.bob",
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
        (f"{MOTOR_IOC}/pmacAxis.pvi.bob", "X1"),
        (f"{MOTOR_IOC}/pmacAxis.pvi.bob", "A"),
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


def test_crawl_link_remote_screen(t01_ctx):
    link = WidgetLink(
        f"{DCAM_IOC}/ADUVC.pvi.bob",
        "DRV",
        WidgetType.ACTION_BUTTON,
        {"P": "BL01C-DI-DCAM-01", "R": ":DRV:"},
    )
    camera = crawl_link(link, "DRV", t01_ctx)
    missing = crawl_link(
        WidgetLink(f"{DCAM_IOC}/missing.pvi.bob", "Missing", link.type, {}),
        "Missing",
        t01_ctx,
    )

    assert (camera.file, camera.display_name, camera.error) == (
        link.file,
        "ADUVC Camera",
        "",
    )
    # The subscreen link is relative and has no macros of its own
    assert camera.children == [
        ScreenNode(f"{DCAM_IOC}/ADUVC_Advanced.pvi.bob", "Advanced", macros=link.macros)
    ]
    assert (missing.exists, missing.children) == (False, [])
    assert missing.error.startswith("Could not fetch screen")


def test_with_screen(t01_ctx):
    motor_ctx = t01_ctx.with_screen(Path("motor1.bob"))

    assert (motor_ctx.screen, motor_ctx.component_name) == (
        Path("motor1.bob"),
        "motor1",
    )
    # Not a component
    assert t01_ctx.with_screen(Path("index.bob")).component_name is None
    # Already inside a component
    assert motor_ctx.with_screen(Path("dcam1.bob")).component_name == "motor1"
    # A remote screen is never a component, but is still the screen being crawled
    remote_ctx = t01_ctx.with_screen(f"{MOTOR_IOC}/motor1.bob")
    assert (remote_ctx.screen, remote_ctx.component_name) == (
        f"{MOTOR_IOC}/motor1.bob",
        None,
    )
