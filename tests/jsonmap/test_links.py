from pathlib import Path

from lxml import objectify

from techui_builder.jsonmap.links import (
    WidgetLink,
    WidgetType,
    assumed_exists,
    extract_links,
    find_local_screen,
    resolve_link_path,
)


def button(name: str, *actions: str, widget_type="action_button") -> str:
    return (
        f'<widget type="{widget_type}"><name>{name}</name>'
        f"<actions>{''.join(actions)}</actions></widget>"
    )


def open_display(file: str, macros: str = "") -> str:
    return (
        f'<action type="open_display"><file>{file}</file>'
        f"<macros>{macros}</macros></action>"
    )


def test_extract_links():
    root = objectify.fromstring(
        '<display version="2.0.0"><name>Display</name>'
        '<widget type="group"><name>Group</name>'
        + button(
            "Button",
            '<action type="write_pv"><pv_name>PV</pv_name></action>',
            open_display(" screen.bob\n", "<P>BL01T-EA-TEST-01</P>"),
            open_display("second.bob"),
        )
        + "</widget>"
        + button("Symbol", open_display("symbol.bob"), widget_type="symbol")
        + '<widget type="symbol"><name>Decoration</name></widget>'
        + button("Legacy", open_display("legacy.opi"))
        + button("Empty", open_display(""))
        + '<widget type="embedded"><name>Embed</name><file>embed.bob</file>'
        "<macros><M>:X</M></macros></widget>"
        '<widget type="navtabs"><name>Tabs</name><tabs>'
        "<tab><name>Tab1</name><file>tab1.bob</file><macros/></tab>"
        "<tab><name>Tab2</name><file>tab2.opi</file><macros/></tab>"
        "</tabs></widget>"
        "</display>"
    )

    assert list(extract_links(root)) == [
        WidgetLink(
            "screen.bob",
            "Button",
            WidgetType.ACTION_BUTTON,
            {"P": "BL01T-EA-TEST-01"},
        ),
        WidgetLink("symbol.bob", "Symbol", WidgetType.SYMBOL, {}),
        WidgetLink("embed.bob", "Embed", WidgetType.EMBEDDED, {"M": ":X"}),
        WidgetLink("tab1.bob", "Tab1", WidgetType.NAVTABS, {}),
    ]


def test_resolve_link_path():
    dest = Path("/beamline/synoptic")
    svc = "bl01t-mo-motor-01"

    assert resolve_link_path("sub/screen.bob", dest, svc) == dest / "sub/screen.bob"
    assert (
        resolve_link_path("$(IOC)/Simple.pvi.bob", dest, svc)
        == dest / f"../{svc}/Simple.pvi.bob"
    )


def test_find_local_screen(tmp_path: Path):
    (tmp_path / "screen.bob").touch()

    assert find_local_screen("screen.bob", tmp_path, "") == tmp_path / "screen.bob"
    for file in ["missing.bob", "", "https://example.invalid/x/screen.bob"]:
        assert find_local_screen(file, tmp_path, "") is None


def test_assumed_exists():
    assert assumed_exists("$(IOC)/x.pvi.bob", {"IOC": "https://example.invalid"})
    assert assumed_exists("https://example.invalid/x/screen.bob", {})
    assert not assumed_exists("missing.bob", {"P": "BL01T-MO-MOTOR-01"})
