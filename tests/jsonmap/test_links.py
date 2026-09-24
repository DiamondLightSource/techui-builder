from pathlib import Path

from lxml import objectify

from techui_builder.jsonmap.links import (
    WidgetLink,
    extract_links,
    is_bob,
    resolve_link,
)
from techui_builder.utils import WidgetType


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


def test_resolve_link():
    screen = Path("/services/synoptic/techui-support/bob/slits/slit.bob")
    macros = {"IOC": "../../../../bl01t-di-cam-01"}

    # Local files are relative to the screen containing the link
    assert resolve_link("../pmac/motor.bob", macros, screen) == Path(
        "/services/synoptic/techui-support/bob/slits/../pmac/motor.bob"
    )
    # Macros are substituted, and unknown ones are left alone
    service_screen = screen.parent / "../../../../bl01t-di-cam-01/ADUVC.pvi.bob"
    assert resolve_link("$(IOC)/ADUVC.pvi.bob", macros, screen) == service_screen
    assert resolve_link("${IOC}/ADUVC.pvi.bob", macros, screen) == service_screen
    assert resolve_link("$(IOC)/x.bob", {}, screen) == screen.parent / "$(IOC)/x.bob"


def test_is_bob():
    assert is_bob("dcam1.bob")
    assert is_bob("$(IOC)/dcam1.bob")
    assert is_bob("../bl01t-di-cam-01/ADUVC.pvi.bob")
    # Screens Phoebus can open but the builder does not crawl
    assert not is_bob("dcam1.opi")
    assert not is_bob("index.html")
    assert not is_bob("")
